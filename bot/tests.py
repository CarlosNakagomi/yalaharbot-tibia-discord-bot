from asgiref.sync import async_to_sync
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import MagicMock, patch
from django.conf import settings
import json
import requests
from pathlib import Path
from config.database import database_from_environment

from bot.models import (
    DiscordUser, Character, CharacterDeath, DiscordUserAndCharacters, EnemyGuild,
    EnemyListConfiguration, EnemyObservation, EnemyOnlineState,
)
from bot.utils import (
    add_character_to_discord_user,
    get_linked_characters,
    get_watched_targets,
    refresh_character,
    set_alert_channel,
    watch_guild,
    watch_world,
    get_online_enemies,
    get_world,
    get_monitored_statuses,
    track_enemy_online_sessions,
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


class TibiaGuild:
    def __init__(self, name, members, world="Antica"):
        self.name = name
        self.members = members
        self.world = world


class TibiaWorld:
    def __init__(self, name, players):
        self.name = name
        self.online_players = players


class CopyableTibiaCharacter(TibiaCharacter):
    def model_copy(self, update):
        return CopyableTibiaCharacter(
            self.name,
            level=self.level,
            vocation=update.get("vocation", self.vocation),
            world=self.world,
        )


class CopyableTibiaWorld(TibiaWorld):
    def model_copy(self, update):
        return CopyableTibiaWorld(self.name, update.get("online_players", self.online_players))


@override_settings(SITE_ACCESS_PASSWORD="site-test-password")
class EnemyListTests(TestCase):
    def setUp(self):
        self.client.post(
            "/api/site-access/login/", {"password": "site-test-password"}, content_type="application/json",
        )

    @patch("bot.utils.WorldParser.from_content")
    @patch("bot.utils.requests.get")
    def test_world_parser_preserves_unknown_vocation_without_failing_scan(self, requests_get, from_content):
        html = """
            <html><body><div class="BoxContent"><table>
              <tr class="Odd"><td>Future Fighter</td><td>321</td><td>Future Vocation</td></tr>
            </table></div></body></html>
        """
        requests_get.return_value.text = html
        parsed_world = CopyableTibiaWorld("Monstera", [
            CopyableTibiaCharacter("Future Fighter", level=321, vocation="None"),
        ])
        from_content.side_effect = [ValueError("unknown vocation"), parsed_world]

        world = get_world("Monstera")

        self.assertEqual(world.online_players[0].vocation, "Future Vocation")
        self.assertEqual(from_content.call_count, 2)
        self.assertIn("<td>None</td>", from_content.call_args_list[1].args[0])

    @patch("bot.utils._tibia_com_blocked_until", 0.0)
    @patch("bot.utils.WorldParser.from_content")
    @patch("bot.utils.requests.get")
    def test_world_request_uses_production_headers_and_tibiapy_parser(
        self, requests_get, from_content,
    ):
        response = MagicMock(status_code=200, text="<html>world</html>")
        requests_get.return_value = response
        from_content.return_value = TibiaWorld("Monstera", [])

        world = get_world("Monstera")

        self.assertEqual(world.name, "Monstera")
        request_kwargs = requests_get.call_args.kwargs
        self.assertEqual(request_kwargs["timeout"], 15)
        self.assertIn("Mozilla/5.0", request_kwargs["headers"]["User-Agent"])
        self.assertIn("Accept-Language", request_kwargs["headers"])
        from_content.assert_called_once_with("<html>world</html>")

    @patch("bot.utils._tibia_com_blocked_until", 0.0)
    @patch("bot.utils.requests.get")
    def test_cloudflare_403_uses_tibiadata_and_one_shared_world_snapshot(self, requests_get):
        forbidden = MagicMock(status_code=403)
        forbidden.raise_for_status.side_effect = requests.HTTPError(response=forbidden)

        world_response = MagicMock(status_code=200)
        world_response.json.return_value = {
            "world": {
                "name": "Monstera",
                "online_players": [
                    {"name": "Enemy Knight", "level": 900, "vocation": "Elite Knight"},
                    {"name": "Friendly Knight", "level": 1000, "vocation": "Elite Knight"},
                ],
            },
        }
        enemy_guild_response = MagicMock(status_code=200)
        enemy_guild_response.json.return_value = {
            "guild": {
                "name": "Watch The Throne", "world": "Monstera",
                "members": [{"name": "Enemy Knight"}],
            },
        }
        friend_guild_response = MagicMock(status_code=200)
        friend_guild_response.json.return_value = {
            "guild": {
                "name": "Unfallen", "world": "Monstera",
                "members": [{"name": "Friendly Knight"}],
            },
        }
        requests_get.side_effect = [
            forbidden, world_response, enemy_guild_response, friend_guild_response,
        ]

        result = get_monitored_statuses(
            "Monstera", {"enemy": ["Watch The Throne"], "friend": ["Unfallen"]},
        )

        self.assertEqual(
            [player["name"] for player in result["monitors"]["enemy"]["players"]],
            ["Enemy Knight"],
        )
        self.assertEqual(
            [player["name"] for player in result["monitors"]["friend"]["players"]],
            ["Friendly Knight"],
        )
        requested_urls = [call.args[0] for call in requests_get.call_args_list]
        self.assertEqual(sum("subtopic=worlds" in url for url in requested_urls), 1)
        self.assertEqual(sum("api.tibiadata.com/v4/world/Monstera" in url for url in requested_urls), 1)
        self.assertEqual(len(requested_urls), 4)

    @patch("bot.utils._tibia_com_blocked_until", 0.0)
    @patch("bot.utils.requests.get")
    def test_non_403_tibia_error_is_not_hidden_by_fallback(self, requests_get):
        unavailable = MagicMock(status_code=503)
        unavailable.raise_for_status.side_effect = requests.HTTPError(response=unavailable)
        requests_get.return_value = unavailable

        with self.assertRaises(requests.HTTPError):
            get_world("Monstera")

        self.assertEqual(requests_get.call_count, 1)

    def test_configuration_and_guild_api(self):
        response = self.client.put(
            "/api/enemy-list/config/",
            {"selected_world": " Antica "},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EnemyListConfiguration.objects.get(pk=1).selected_world, "Antica")

        response = self.client.post(
            "/api/enemy-guilds/",
            {"name": "Enemy Team"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(EnemyGuild.objects.filter(name="Enemy Team").exists())

        duplicate = self.client.post(
            "/api/enemy-guilds/",
            {"name": "enemy team"},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 400)

    @patch("bot.utils.get_guild")
    @patch("bot.utils.get_world")
    def test_online_enemies_cross_references_names_case_insensitively(self, get_world, get_guild):
        get_world.return_value = TibiaWorld("Antica", [
            TibiaCharacter("Enemy One", level=400, vocation="Elite Knight"),
            TibiaCharacter("Neutral Player", level=500),
        ])
        get_guild.return_value = TibiaGuild("Enemy Team", [TibiaCharacter("enemy one")])

        result = get_online_enemies("Antica", ["Enemy Team"])

        self.assertEqual(result["world_online_count"], 2)
        self.assertEqual(result["enemy_online_count"], 1)
        self.assertEqual(result["enemies"][0]["name"], "Enemy One")
        self.assertEqual(result["enemies"][0]["guilds"], ["Enemy Team"])

    @patch("bot.views.get_online_enemies")
    def test_status_endpoint_uses_saved_configuration(self, get_online_enemies_mock):
        EnemyListConfiguration.objects.create(pk=1, selected_world="Antica")
        EnemyGuild.objects.create(name="Enemy Team")
        get_online_enemies_mock.return_value = {
            "world": "Antica", "world_online_count": 1, "enemy_online_count": 0,
            "enemies": [], "guilds": [],
        }

        response = self.client.get("/api/enemy-list/status/")

        self.assertEqual(response.status_code, 200)
        get_online_enemies_mock.assert_called_once_with("Antica", ["Enemy Team"])

    @patch("bot.utils.get_guild")
    @patch("bot.utils.get_world")
    def test_combined_monitors_reuse_world_snapshot_and_keep_rosters_separate(self, get_world, get_guild):
        get_world.return_value = TibiaWorld("Monstera", [
            TibiaCharacter("Enemy Knight", level=900, vocation="Elite Knight"),
            TibiaCharacter("Friendly Knight", level=1000, vocation="Elite Knight"),
            TibiaCharacter("Offline Neutral", level=800, vocation="Royal Paladin"),
        ])
        get_guild.side_effect = [
            TibiaGuild("Watch The Throne", [TibiaCharacter("Enemy Knight"), TibiaCharacter("Offline Enemy")], "Monstera"),
            TibiaGuild("Unfallen", [TibiaCharacter("Friendly Knight"), TibiaCharacter("Offline Friend")], "Monstera"),
        ]

        result = get_monitored_statuses(
            "Monstera", {"enemy": ["Watch The Throne"], "friend": ["Unfallen"]},
        )

        self.assertEqual(get_world.call_count, 1)
        self.assertEqual([player["name"] for player in result["monitors"]["enemy"]["players"]], ["Enemy Knight"])
        self.assertEqual([player["name"] for player in result["monitors"]["friend"]["players"]], ["Friendly Knight"])
        self.assertEqual(result["monitors"]["enemy"]["guilds"][0]["name"], "Watch The Throne")
        self.assertEqual(result["monitors"]["friend"]["guilds"][0]["name"], "Unfallen")

    @patch("bot.views.get_monitored_statuses")
    def test_combined_status_endpoint_identifies_enemy_and_friend(self, get_statuses):
        get_statuses.return_value = {
            "world": "Monstera", "world_online_count": 2,
            "monitors": {
                "enemy": {"online_count": 1, "players": [], "guilds": [{"name": "Watch The Throne"}]},
                "friend": {"online_count": 1, "players": [], "guilds": [{"name": "Unfallen"}]},
            },
        }

        response = self.client.get("/api/monitors/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["monitors"]["enemy"]["guilds"][0]["name"], "Watch The Throne")
        self.assertEqual(response.json()["monitors"]["friend"]["guilds"][0]["name"], "Unfallen")
        get_statuses.assert_called_once_with(
            "Monstera", {"enemy": ["Watch The Throne"], "friend": ["Unfallen"]},
        )


class EnemyOnlineSessionTests(TestCase):
    def enemy(self, name="Mago Malvado"):
        return {"name": name, "level": 500, "vocation": "Master Sorcerer", "guilds": ["Enemy Team"]}

    def test_initial_observation_starts_session_and_refresh_does_not_reset_it(self):
        first_observation = timezone.now()
        first = track_enemy_online_sessions("Antica", [self.enemy()], first_observation)
        second = track_enemy_online_sessions("Antica", [self.enemy()], first_observation + timedelta(minutes=5))

        self.assertEqual(first[0]["online_since"], first_observation.isoformat())
        self.assertEqual(second[0]["online_since"], first_observation.isoformat())
        self.assertEqual(EnemyOnlineState.objects.get().session_started_at, first_observation)

    def test_existing_database_session_survives_new_monitor_process_and_browser_requests(self):
        session_start = timezone.now() - timedelta(minutes=20)
        EnemyOnlineState.objects.create(
            world="Antica", world_key="antica", character_name="Mago Malvado",
            character_key="mago malvado", is_online=True, session_started_at=session_start,
        )

        browser_refresh = track_enemy_online_sessions("Antica", [self.enemy()], timezone.now())
        later_backend_process = track_enemy_online_sessions(
            "Antica", [self.enemy()], timezone.now() + timedelta(minutes=5),
        )

        self.assertEqual(browser_refresh[0]["online_since"], session_start.isoformat())
        self.assertEqual(later_backend_process[0]["online_since"], session_start.isoformat())

    def test_legacy_online_state_without_timestamp_starts_on_next_observation(self):
        EnemyOnlineState.objects.create(
            world="Antica", world_key="antica", character_name="Mago Malvado",
            character_key="mago malvado", is_online=True, session_started_at=None,
        )
        observed_at = timezone.now()

        result = track_enemy_online_sessions("Antica", [self.enemy()], observed_at)

        self.assertEqual(result[0]["online_since"], observed_at.isoformat())

    def test_friend_session_is_persisted_and_does_not_overwrite_enemy_session(self):
        enemy_start = timezone.now() - timedelta(minutes=10)
        friend_start = timezone.now()
        track_enemy_online_sessions("Monstera", [self.enemy()], enemy_start, monitor_type="enemy")
        track_enemy_online_sessions("Monstera", [self.enemy()], friend_start, monitor_type="friend")

        states = EnemyOnlineState.objects.order_by("monitor_type")
        self.assertEqual(states.count(), 2)
        self.assertEqual(states.get(monitor_type="enemy").session_started_at, enemy_start)
        self.assertEqual(states.get(monitor_type="friend").session_started_at, friend_start)

        track_enemy_online_sessions("Monstera", [], friend_start + timedelta(minutes=1), monitor_type="friend")
        self.assertTrue(EnemyOnlineState.objects.get(monitor_type="enemy").is_online)
        self.assertFalse(EnemyOnlineState.objects.get(monitor_type="friend").is_online)

        next_login = friend_start + timedelta(minutes=2)
        result = track_enemy_online_sessions("Monstera", [self.enemy()], next_login, monitor_type="friend")
        self.assertEqual(result[0]["online_since"], next_login.isoformat())

    def test_logout_ends_session_and_later_login_starts_new_session(self):
        track_enemy_online_sessions("Antica", [self.enemy()])
        track_enemy_online_sessions("Antica", [])
        state = EnemyOnlineState.objects.get()
        self.assertFalse(state.is_online)
        self.assertIsNone(state.session_started_at)

        first_login = timezone.now()
        result = track_enemy_online_sessions("Antica", [self.enemy()], first_login)
        self.assertEqual(result[0]["online_since"], first_login.isoformat())

        ordinary_refresh = first_login + timedelta(minutes=5)
        result = track_enemy_online_sessions("Antica", [self.enemy()], ordinary_refresh)
        self.assertEqual(result[0]["online_since"], first_login.isoformat())

        track_enemy_online_sessions("Antica", [])
        later_login = first_login + timedelta(hours=1)
        result = track_enemy_online_sessions("Antica", [self.enemy()], later_login)
        self.assertEqual(result[0]["online_since"], later_login.isoformat())


@override_settings(ENEMY_NOTES_EDIT_PASSWORD="test-only-password", SITE_ACCESS_PASSWORD="site-test-password")
class EnemyObservationTests(TestCase):
    endpoint = "/api/enemy-list/observations/"

    def setUp(self):
        self.client.post(
            "/api/site-access/login/", {"password": "site-test-password"}, content_type="application/json",
        )

    def test_observations_are_publicly_readable_and_password_is_never_returned(self):
        EnemyObservation.objects.create(
            character_name="Mago Malvado", character_key="mago malvado", observation="Shotcaller",
        )
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["observation"], "Shotcaller")
        self.assertNotIn("password", str(response.json()).lower())
        self.assertNotIn("test-only-password", str(response.content))

    def test_correct_password_creates_and_case_insensitively_updates(self):
        created = self.client.put(
            self.endpoint,
            {"character_name": "Mago Malvado", "observation": "First", "password": "test-only-password"},
            content_type="application/json",
        )
        updated = self.client.put(
            self.endpoint,
            {"character_name": "MAGO MALVADO", "observation": "Updated", "password": "test-only-password"},
            content_type="application/json",
        )

        self.assertEqual(created.status_code, 200)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(EnemyObservation.objects.count(), 1)
        self.assertEqual(EnemyObservation.objects.get().observation, "Updated")
        self.assertEqual(EnemyObservation.objects.get().character_name, "Mago Malvado")

    def test_incorrect_password_cannot_create_update_or_delete(self):
        EnemyObservation.objects.create(
            character_name="Mago Malvado", character_key="mago malvado", observation="Keep me",
        )
        update = self.client.put(
            self.endpoint,
            {"character_name": "Mago Malvado", "observation": "Changed", "password": "wrong"},
            content_type="application/json",
        )
        delete = self.client.delete(
            self.endpoint,
            {"character_name": "Mago Malvado", "password": "wrong"},
            content_type="application/json",
        )

        self.assertEqual(update.status_code, 403)
        self.assertEqual(delete.status_code, 403)
        self.assertEqual(EnemyObservation.objects.get().observation, "Keep me")

    def test_correct_password_can_clear_observation(self):
        EnemyObservation.objects.create(
            character_name="Mago Malvado", character_key="mago malvado", observation="Clear me",
        )
        response = self.client.delete(
            self.endpoint,
            {"character_name": "mAgO mAlVaDo", "password": "test-only-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(EnemyObservation.objects.exists())

    @patch("bot.views.get_online_enemies")
    def test_observation_survives_online_list_refresh(self, get_online_enemies_mock):
        EnemyListConfiguration.objects.create(pk=1, selected_world="Antica")
        EnemyGuild.objects.create(name="Enemy Team")
        note = EnemyObservation.objects.create(
            character_name="Mago Malvado", character_key="mago malvado", observation="Persistent",
        )
        get_online_enemies_mock.return_value = {
            "world": "Antica", "world_online_count": 0, "enemy_online_count": 0,
            "enemies": [], "guilds": [],
        }

        self.client.get("/api/enemy-list/status/")
        note.refresh_from_db()
        self.assertEqual(note.observation, "Persistent")


@override_settings(
    SITE_ACCESS_PASSWORD="site-test-password",
    ENEMY_NOTES_EDIT_PASSWORD="different-note-password",
)
class SiteAccessTests(TestCase):
    def test_site_password_is_not_present_in_frontend_source(self):
        frontend_source = Path(settings.BASE_DIR / "frontend" / "src")
        source_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in frontend_source.rglob("*")
            if path.suffix in {".js", ".jsx"}
        )
        self.assertNotIn(settings.SITE_ACCESS_PASSWORD, source_text)

    def test_health_is_public_and_non_sensitive(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        serialized = json.dumps(response.json())
        self.assertNotIn(settings.SITE_ACCESS_PASSWORD, serialized)
        self.assertNotIn(settings.ENEMY_NOTES_EDIT_PASSWORD, serialized)

    def test_monitor_data_requires_site_access(self):
        response = self.client.get("/api/monitors/status/")
        self.assertEqual(response.status_code, 401)

    def test_incorrect_password_is_rejected_without_returning_secret(self):
        response = self.client.post(
            "/api/site-access/login/", {"password": "wrong"}, content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(settings.SITE_ACCESS_PASSWORD, response.content.decode())

    @patch("bot.views.get_monitored_statuses")
    def test_correct_password_grants_monitor_access_and_logout_revokes_it(self, get_statuses):
        get_statuses.return_value = {
            "world": "Monstera", "world_online_count": 0,
            "monitors": {
                "enemy": {"online_count": 0, "players": [], "guilds": []},
                "friend": {"online_count": 0, "players": [], "guilds": []},
            },
        }
        login = self.client.post(
            "/api/site-access/login/", {"password": "site-test-password"}, content_type="application/json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn(settings.SITE_ACCESS_COOKIE_NAME, login.cookies)
        self.assertTrue(login.cookies[settings.SITE_ACCESS_COOKIE_NAME]["httponly"])
        self.assertNotIn(settings.SITE_ACCESS_PASSWORD, login.content.decode())
        self.assertEqual(self.client.get("/api/monitors/status/").status_code, 200)

        logout = self.client.post("/api/site-access/logout/")
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get("/api/monitors/status/").status_code, 401)

    def test_site_password_does_not_grant_observation_editing(self):
        self.client.post(
            "/api/site-access/login/", {"password": "site-test-password"}, content_type="application/json",
        )
        response = self.client.put(
            "/api/enemy-list/observations/",
            {"character_name": "Friendly Knight", "observation": "Note", "password": "site-test-password"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class DatabaseConfigurationTests(TestCase):
    @patch.dict("os.environ", {"DATABASE_URL": "", "DB_ENGINE": "django.db.backends.sqlite3", "DB_NAME": "db.sqlite3"}, clear=False)
    def test_local_database_defaults_to_sqlite(self):
        database = database_from_environment(Path("/tmp/project"))
        self.assertEqual(database["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(database["NAME"], Path("/tmp/project/db.sqlite3"))

    @patch.dict(
        "os.environ",
        {"DATABASE_URL": "postgresql://railway_user:railway_password@postgres.internal:5432/railway"},
        clear=False,
    )
    def test_production_database_uses_database_url(self):
        database = database_from_environment(Path("/tmp/project"))
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["HOST"], "postgres.internal")
        self.assertEqual(database["NAME"], "railway")
