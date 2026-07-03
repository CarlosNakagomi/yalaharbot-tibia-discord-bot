from rest_framework import serializers
from .models import DiscordUser, Character, DiscordUserAndCharacters

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