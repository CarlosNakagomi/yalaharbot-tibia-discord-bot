from asgiref.sync import async_to_sync
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from bot.models import DiscordUser, Character, CharacterDeath, DiscordUserAndCharacters
from bot.utils import (
    add_character_to_discord_user,
    get_linked_characters,
    get_watched_targets,
    refresh_character,
    set_alert_channel,
    watch_guild,
    watch_world,
)


class TibiaKiller:
    def __init__(self, name):
        self.name = name


class TibiaDeath:
    def __init__(self, level, time, killers):
        self.level = level
        self.time = time
        self.killers = [TibiaKiller(killer) for killer in killers]


class TibiaCharacter:
    def __init__(self, name, level=100, vocation="Elite Knight", world="Antica", other_characters=None, deaths=None):
        self.name = name
        self.level = level
        self.vocation = vocation
        self.world = world
        self.other_characters = other_characters or []
        self.deaths = deaths or []


class CharacterLinkingTests(TestCase):
    @patch("bot.utils.get_character")
    def test_add_character_to_discord_user_stores_tibia_data(self, get_character):
        get_character.return_value = TibiaCharacter(
            "Knight One",
            level=250,
            vocation="Elite Knight",
            world="Lobera",
            other_characters=[TibiaCharacter("Druid Two")],
        )

        discord_user, character = async_to_sync(add_character_to_discord_user)(12345, "Knight One")

        self.assertEqual(discord_user.User, "12345")
        self.assertEqual(character.name, "Knight One")
        self.assertEqual(character.level, 250)
        self.assertEqual(character.vocation, "Elite Knight")
        self.assertEqual(character.world, "Lobera")
        self.assertEqual(character.other_characters, "Druid Two")
        self.assertEqual(CharacterDeath.objects.count(), 0)
        self.assertTrue(
            DiscordUserAndCharacters.objects.filter(discord_user=discord_user, character=character).exists()
        )

    def test_get_linked_characters_returns_characters_for_discord_user(self):
        discord_user = DiscordUser.objects.create(User="12345")
        other_user = DiscordUser.objects.create(User="67890")
        character = Character.objects.create(
            name="Knight One",
            accountid=discord_user,
            level=250,
            vocation="Elite Knight",
            world="Lobera",
            other_characters="",
        )
        other_character = Character.objects.create(
            name="Sorcerer Two",
            accountid=other_user,
            level=180,
            vocation="Master Sorcerer",
            world="Lobera",
            other_characters="",
        )
        DiscordUserAndCharacters.objects.create(discord_user=discord_user, character=character)
        DiscordUserAndCharacters.objects.create(discord_user=other_user, character=other_character)

        characters = async_to_sync(get_linked_characters)(12345)

        self.assertEqual(characters, [character])

    @patch("bot.utils.get_character")
    def test_refresh_character_baselines_existing_deaths_without_reporting_them(self, get_character):
        discord_user = DiscordUser.objects.create(User="12345")
        character = Character.objects.create(
            name="Knight One",
            accountid=discord_user,
            level=250,
            vocation="Elite Knight",
            world="Lobera",
            other_characters="",
        )
        death_time = timezone.now()
        get_character.return_value = TibiaCharacter(
            "Knight One",
            level=251,
            deaths=[TibiaDeath(250, death_time, ["Demon"])],
        )

        result = async_to_sync(refresh_character)(character.id)

        self.assertEqual(result.previous_level, 250)
        self.assertEqual(result.character.level, 251)
        self.assertEqual(result.new_deaths, [])
        self.assertEqual(CharacterDeath.objects.count(), 1)

    @patch("bot.utils.get_character")
    def test_refresh_character_reports_deaths_after_baseline_exists(self, get_character):
        discord_user = DiscordUser.objects.create(User="12345")
        character = Character.objects.create(
            name="Knight One",
            accountid=discord_user,
            level=250,
            vocation="Elite Knight",
            world="Lobera",
            other_characters="",
        )
        old_death_time = timezone.now() - timedelta(days=1)
        new_death_time = timezone.now()
        get_character.return_value = TibiaCharacter(
            "Knight One",
            level=250,
            deaths=[TibiaDeath(250, old_death_time, ["Demon"])],
        )
        async_to_sync(refresh_character)(character.id)

        get_character.return_value = TibiaCharacter(
            "Knight One",
            level=252,
            deaths=[
                TibiaDeath(252, new_death_time, ["Dragon Lord"]),
                TibiaDeath(250, old_death_time, ["Demon"]),
            ],
        )
        result = async_to_sync(refresh_character)(character.id)

        self.assertEqual(result.previous_level, 250)
        self.assertEqual(result.character.level, 252)
        self.assertEqual([death.killers for death in result.new_deaths], ["Dragon Lord"])
        self.assertEqual(CharacterDeath.objects.count(), 2)

    def test_server_settings_store_watched_targets(self):
        async_to_sync(set_alert_channel)(1030000633614450698, 222)
        async_to_sync(watch_world)(1030000633614450698, "Lobera")
        async_to_sync(watch_guild)(1030000633614450698, "Yalahar")

        settings, worlds, guilds = async_to_sync(get_watched_targets)(1030000633614450698)

        self.assertEqual(settings.alert_channel_id, "222")
        self.assertEqual(worlds, ["Lobera"])
        self.assertEqual(guilds, ["Yalahar"])
