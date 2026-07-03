from django.db import models

class DiscordUser(models.Model):
    User = models.CharField(max_length=100, unique=True, default="Unknown User")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.User


class Character(models.Model):
    name = models.CharField(max_length=100, unique=True)
    accountid = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)  # Changed from Account to DiscordUser
    level = models.IntegerField()
    vocation = models.CharField(max_length=50)
    world = models.CharField(max_length=50, db_index=True)
    other_characters = models.CharField(max_length=1000)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DiscordUserAndCharacters(models.Model):
    discord_user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Discord User {self.discord_user.User} - Character {self.character.name}"


class CharacterDeath(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="deaths")
    level = models.IntegerField()
    died_at = models.DateTimeField()
    killers = models.TextField()
    fingerprint = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-died_at"]

    def __str__(self):
        return f"{self.character.name} died at level {self.level}"


class DiscordServerSettings(models.Model):
    guild_id = models.CharField(max_length=32, unique=True)
    alert_channel_id = models.CharField(max_length=32)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Discord server {self.guild_id}"


class WatchedWorld(models.Model):
    settings = models.ForeignKey(DiscordServerSettings, on_delete=models.CASCADE, related_name="watched_worlds")
    name = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["settings", "name"]
        ordering = ["name"]

    def __str__(self):
        return self.name


class WatchedGuild(models.Model):
    settings = models.ForeignKey(DiscordServerSettings, on_delete=models.CASCADE, related_name="watched_guilds")
    name = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["settings", "name"]
        ordering = ["name"]

    def __str__(self):
        return self.name
