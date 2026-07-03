# bot/utils.py

import requests
import tibiapy
from tibiapy.parsers import CharacterParser
from bot.models import DiscordUser, Character, DiscordUserAndCharacters
import discord
from asgiref.sync import sync_to_async


def get_character(name):
    url = tibiapy.urls.get_character_url(name)
    r = requests.get(url)
    content = r.text
    character = CharacterParser.from_content(content)
    return character

@sync_to_async
def update_or_create_character(name, level, vocation, world, other_characters):
    discord_user, _ = DiscordUser.objects.get_or_create(User=name)  # Assuming character name is the Discord user's name
    return Character.objects.update_or_create(
        name=name,
        defaults={
            'accountid': discord_user,
            'level': level,
            'vocation': str(vocation),
            'world': world,
            'other_characters': other_characters
        }
    )

@sync_to_async
def add_character_to_discord_user(discord_id, character_name):
    discord_user, created = DiscordUser.objects.get_or_create(User=discord_id)
    character, created = Character.objects.get_or_create(
        name=character_name,
        defaults={
            'accountid': discord_user,
            'level': 1,
            'vocation': 'None',
            'world': 'Unknown',
            'other_characters': ''
        }
    )
    DiscordUserAndCharacters.objects.get_or_create(discord_user=discord_user, character=character)
    return discord_user, character
