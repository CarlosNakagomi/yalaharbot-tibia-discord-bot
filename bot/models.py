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
