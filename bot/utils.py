import requests
import tibiapy
from dataclasses import dataclass
from hashlib import sha256
from tibiapy.parsers import CharacterParser, GuildParser, WorldParser
from tibiapy.enums import Vocation
from tibiapy.utils import clean_text, parse_tibiacom_content
from bot.models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
    EnemyOnlineState,
)
from django.db import transaction
from django.utils import timezone
from asgiref.sync import sync_to_async


@dataclass
class CharacterRefreshResult:
    character: Character
    previous_level: int
    new_deaths: list[CharacterDeath]


def get_character(name):
    url = tibiapy.urls.get_character_url(name)
    r = requests.get(url)
    content = r.text
    character = CharacterParser.from_content(content)
    return character


def get_guild(name, timeout=15):
    url = tibiapy.urls.get_guild_url(name)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return GuildParser.from_content(response.text)


def get_world(name, timeout=15):
    url = tibiapy.urls.get_world_url(name)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    try:
        return WorldParser.from_content(response.text)
    except ValueError:
        # Tibia.py models intentionally validate vocation names. If Tibia adds a
        # vocation before the library is updated, preserve its real label while
        # allowing the rest of the world page to be parsed normally.
        sanitized_content, unknown_vocations = _sanitize_unknown_online_vocations(response.text)
        if not unknown_vocations:
            raise
        world = WorldParser.from_content(sanitized_content)
        return _restore_unknown_online_vocations(world, unknown_vocations)


def _sanitize_unknown_online_vocations(content):
    parsed_content = parse_tibiacom_content(content)
    known_vocations = {vocation.value for vocation in Vocation}
    unknown_vocations = {}

    for row in parsed_content.select("tr.Odd, tr.Even"):
        columns = row.select("td")
        if len(columns) != 3:
            continue
        name, level, vocation = (clean_text(column) for column in columns)
        if not level.isdigit() or vocation in known_vocations:
            continue
        unknown_vocations[name.casefold()] = vocation
        columns[2].string = Vocation.NONE.value

    return str(parsed_content), unknown_vocations


def _restore_unknown_online_vocations(world, unknown_vocations):
    if world is None:
        return None

    online_players = []
    for player in world.online_players:
        vocation = unknown_vocations.get(player.name.casefold())
        online_players.append(player.model_copy(update={"vocation": vocation}) if vocation else player)
    return world.model_copy(update={"online_players": online_players})


def get_monitored_guild_status(world, guild_names):
    """Match guild rosters against an already-fetched Tibia world snapshot."""
    online_by_name = {player.name.casefold(): player for player in world.online_players}
    monitored_players = {}
    guild_summaries = []

    for guild_name in guild_names:
        try:
            guild = get_guild(guild_name)
            if guild is None:
                raise ValueError("Guild was not found.")

            members = list(guild.members)
            matches = 0
            for member in members:
                player = online_by_name.get(member.name.casefold())
                if player is None:
                    continue
                matches += 1
                key = player.name.casefold()
                monitored_player = monitored_players.setdefault(key, {
                    "name": player.name,
                    "level": player.level,
                    "vocation": str(player.vocation),
                    "guilds": [],
                })
                monitored_player["guilds"].append(guild.name)

            guild_summaries.append({
                "name": guild.name,
                "world": guild.world,
                "member_count": len(members),
                "online_count": matches,
                "error": None,
            })
        except (requests.RequestException, ValueError) as exc:
            guild_summaries.append({
                "name": guild_name,
                "world": None,
                "member_count": 0,
                "online_count": 0,
                "error": str(exc),
            })

    online_players = sorted(
        monitored_players.values(), key=lambda item: (-item["level"], item["name"].casefold()),
    )
    return {
        "online_count": len(online_players),
        "players": online_players,
        "guilds": guild_summaries,
    }


def get_monitored_statuses(world_name, monitor_guilds):
    """Fetch one world snapshot and derive any number of named monitor datasets."""
    world = get_world(world_name)
    if world is None:
        raise ValueError(f"World '{world_name}' was not found.")
    return {
        "world": world.name,
        "world_online_count": len(world.online_players),
        "monitors": {
            monitor_type: get_monitored_guild_status(world, guild_names)
            for monitor_type, guild_names in monitor_guilds.items()
        },
    }


def get_online_enemies(world_name, guild_names):
    """Backward-compatible enemy-only status using the shared matcher."""
    payload = get_monitored_statuses(world_name, {"enemy": guild_names})
    enemy = payload["monitors"]["enemy"]
    return {
        "world": payload["world"],
        "world_online_count": payload["world_online_count"],
        "enemy_online_count": enemy["online_count"],
        "enemies": enemy["players"],
        "guilds": enemy["guilds"],
    }


@transaction.atomic
def track_enemy_online_sessions(world_name, enemies, observed_at=None, monitor_type="enemy"):
    """Attach observed-online timestamps within an enemy/friend monitor context."""
    observed_at = observed_at or timezone.now()
    world_key = world_name.casefold()
    online_keys = []
    states = {}

    for enemy in enemies:
        character_key = enemy["name"].casefold()
        online_keys.append(character_key)
        state, created = EnemyOnlineState.objects.select_for_update().get_or_create(
            monitor_type=monitor_type,
            world_key=world_key,
            character_key=character_key,
            defaults={
                "world": world_name,
                "character_name": enemy["name"],
                "is_online": True,
                "session_started_at": observed_at,
            },
        )
        if not created:
            state.world = world_name
            state.character_name = enemy["name"]
            if not state.is_online:
                state.is_online = True
                state.session_started_at = observed_at
            elif state.session_started_at is None:
                # Upgrade legacy/unknown active states on their first successful
                # observation under observed-online timing semantics.
                state.session_started_at = observed_at
            state.save()
        states[character_key] = state

    offline_states = EnemyOnlineState.objects.select_for_update().filter(
        monitor_type=monitor_type, world_key=world_key, is_online=True,
    )
    if online_keys:
        offline_states = offline_states.exclude(character_key__in=online_keys)
    offline_states.update(is_online=False, session_started_at=None, last_observed_at=observed_at)

    return [
        {**enemy, "online_since": states[enemy["name"].casefold()].session_started_at.isoformat()
         if states[enemy["name"].casefold()].session_started_at else None}
        for enemy in enemies
    ]


def character_names(characters):
    return [character.name for character in characters]


def other_character_names(character):
    return ", ".join(character_names(character.other_characters))


def death_killers(death):
    return ", ".join(killer.name for killer in death.killers)


def death_fingerprint(character_name, death):
    raw = f"{character_name}|{death.time.isoformat()}|{death.level}|{death_killers(death)}"
    return sha256(raw.encode("utf-8")).hexdigest()


def store_character_deaths(character, tibia_character):
    created_deaths = []
    for death in tibia_character.deaths:
        character_death, created = CharacterDeath.objects.get_or_create(
            fingerprint=death_fingerprint(tibia_character.name, death),
            defaults={
                "character": character,
                "level": death.level,
                "died_at": death.time,
                "killers": death_killers(death),
            },
        )
        if created:
            created_deaths.append(character_death)
    return created_deaths


def save_character_for_user(discord_user, character):
    saved_character, created = Character.objects.update_or_create(
        name=character.name,
        defaults={
            "accountid": discord_user,
            "level": character.level,
            "vocation": str(character.vocation),
            "world": character.world,
            "other_characters": other_character_names(character),
        }
    )
    store_character_deaths(saved_character, character)
    return saved_character, created


@sync_to_async
def update_or_create_character(name, level, vocation, world, other_characters):
    discord_user, _ = DiscordUser.objects.get_or_create(User=name)
    return Character.objects.update_or_create(
        name=name,
        defaults={
            "accountid": discord_user,
            "level": level,
            "vocation": str(vocation),
            "world": world,
            "other_characters": other_characters,
        }
    )


@sync_to_async
def save_tibia_character(character):
    discord_user, _ = DiscordUser.objects.get_or_create(User=character.name)
    return save_character_for_user(discord_user, character)


@sync_to_async
def add_character_to_discord_user(discord_id, character_name):
    tibia_character = get_character(character_name)
    if tibia_character is None:
        raise ValueError(f"Character '{character_name}' not found.")

    discord_user, _ = DiscordUser.objects.get_or_create(User=str(discord_id))
    character, _ = save_character_for_user(discord_user, tibia_character)
    DiscordUserAndCharacters.objects.get_or_create(discord_user=discord_user, character=character)
    return discord_user, character


@sync_to_async
def get_linked_characters(discord_id):
    return list(
        Character.objects.filter(
            discorduserandcharacters__discord_user__User=str(discord_id)
        )
        .order_by("name")
        .distinct()
    )


@sync_to_async
def get_recent_deaths(character_name, limit=5):
    return list(
        CharacterDeath.objects.filter(character__name__iexact=character_name)
        .select_related("character")
        .order_by("-died_at")[:limit]
    )


@sync_to_async
def get_top_characters(limit=10):
    return list(Character.objects.order_by("-level", "name")[:limit])


@sync_to_async
def get_recent_character_deaths(limit=10):
    return list(CharacterDeath.objects.select_related("character").order_by("-died_at")[:limit])


@sync_to_async
def set_alert_channel(guild_id, channel_id):
    settings, _ = DiscordServerSettings.objects.update_or_create(
        guild_id=str(guild_id),
        defaults={"alert_channel_id": str(channel_id)},
    )
    return settings


@sync_to_async
def get_server_settings(guild_id):
    return DiscordServerSettings.objects.get(guild_id=str(guild_id))


@sync_to_async
def watch_world(guild_id, world_name):
    settings = DiscordServerSettings.objects.get(guild_id=str(guild_id))
    watched_world, _ = WatchedWorld.objects.get_or_create(settings=settings, name=world_name)
    return watched_world


@sync_to_async
def unwatch_world(guild_id, world_name):
    settings = DiscordServerSettings.objects.get(guild_id=str(guild_id))
    return WatchedWorld.objects.filter(settings=settings, name__iexact=world_name).delete()[0]


@sync_to_async
def watch_guild(guild_id, guild_name):
    settings = DiscordServerSettings.objects.get(guild_id=str(guild_id))
    watched_guild, _ = WatchedGuild.objects.get_or_create(settings=settings, name=guild_name)
    return watched_guild


@sync_to_async
def unwatch_guild(guild_id, guild_name):
    settings = DiscordServerSettings.objects.get(guild_id=str(guild_id))
    return WatchedGuild.objects.filter(settings=settings, name__iexact=guild_name).delete()[0]


@sync_to_async
def get_watched_targets(guild_id):
    settings = DiscordServerSettings.objects.get(guild_id=str(guild_id))
    worlds = list(settings.watched_worlds.order_by("name").values_list("name", flat=True))
    guilds = list(settings.watched_guilds.order_by("name").values_list("name", flat=True))
    return settings, worlds, guilds


@sync_to_async
def refresh_all_tracked_characters():
    settings = list(DiscordServerSettings.objects.all())
    character_ids = list(Character.objects.order_by("id").values_list("id", flat=True))
    return settings, character_ids


@sync_to_async
def refresh_character(character_id):
    character = Character.objects.get(id=character_id)
    tibia_character = get_character(character.name)
    if tibia_character is None:
        raise ValueError(f"Character '{character.name}' not found.")

    previous_level = character.level
    had_death_baseline = CharacterDeath.objects.filter(character=character).exists()
    new_deaths = store_character_deaths(character, tibia_character)

    character.level = tibia_character.level
    character.vocation = str(tibia_character.vocation)
    character.world = tibia_character.world
    character.other_characters = other_character_names(tibia_character)
    character.save()

    return CharacterRefreshResult(
        character=character,
        previous_level=previous_level,
        new_deaths=new_deaths if had_death_baseline else [],
    )
