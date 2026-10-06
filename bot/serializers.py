from rest_framework import serializers
from .models import (
    DiscordUser,
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
    EnemyGuild,
    EnemyListConfiguration,
    EnemyObservation,
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


class EnemyListConfigurationSerializer(serializers.ModelSerializer):
    selected_world = serializers.CharField(max_length=50, allow_blank=False)

    class Meta:
        model = EnemyListConfiguration
        fields = ['selected_world', 'last_updated']
        read_only_fields = ['last_updated']

    def validate_selected_world(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A Tibia world is required.')
        return value


class EnemyGuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnemyGuild
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A guild name is required.')
        if EnemyGuild.objects.filter(name__iexact=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError('This enemy guild is already configured.')
        return value


class EnemyObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnemyObservation
        fields = ['character_name', 'observation', 'updated_at']
        read_only_fields = ['updated_at']

    def validate_character_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A character name is required.')
        return value

    def validate_observation(self, value):
        value = value.strip()
        if len(value) > 2000:
            raise serializers.ValidationError('Observation must be 2000 characters or fewer.')
        return value
