import requests
import tibiapy
from dataclasses import dataclass
from hashlib import sha256
from tibiapy.parsers import CharacterParser, GuildParser, WorldParser
from bot.models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
)
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


def get_guild(name):
    url = tibiapy.urls.get_guild_url(name)
    response = requests.get(url)
    return GuildParser.from_content(response.text)


def get_world(name):
    url = tibiapy.urls.get_world_url(name)
    response = requests.get(url)
    return WorldParser.from_content(response.text)


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
