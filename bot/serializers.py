from rest_framework import serializers
from .models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
)

class DiscordUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordUser
        fields = ['id', 'User', 'last_updated']

class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'name', 'accountid', 'level', 'vocation', 'world', 'other_characters', 'last_updated']

class DiscordUserAndCharactersSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordUserAndCharacters
        fields = ['id', 'discord_user', 'character', 'last_updated']


class CharacterDeathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterDeath
        fields = ['id', 'character', 'level', 'died_at', 'killers', 'fingerprint', 'created_at']


class DiscordServerSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordServerSettings
        fields = ['id', 'guild_id', 'alert_channel_id', 'last_updated']


class WatchedWorldSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedWorld
        fields = ['id', 'settings', 'name', 'last_updated']


class WatchedGuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedGuild
        fields = ['id', 'settings', 'name', 'last_updated']
