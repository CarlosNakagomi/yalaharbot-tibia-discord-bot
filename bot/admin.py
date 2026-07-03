from django.contrib import admin

from bot.models import (
    Character,
    CharacterDeath,
    DiscordServerSettings,
    DiscordUser,
    DiscordUserAndCharacters,
    WatchedGuild,
    WatchedWorld,
)

admin.site.register(DiscordUser)
admin.site.register(Character)
admin.site.register(DiscordUserAndCharacters)
admin.site.register(CharacterDeath)
admin.site.register(DiscordServerSettings)
admin.site.register(WatchedGuild)
admin.site.register(WatchedWorld)
