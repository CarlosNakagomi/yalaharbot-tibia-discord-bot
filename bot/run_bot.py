import os
import sys
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Importar directamente el comando desde `add_command.py`

# Configuración de logging

logging.basicConfig(level=logging.DEBUG)

# Añadir la ruta del proyecto para que Python pueda encontrar los módulos locales.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de Django - establecer la variable DJANGO_SETTINGS_MODULE antes de importar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()
from bot.commands.add_command import add
from bot.commands.lookup_command import setup as setup_lookup_commands
from bot.commands.server_command import setup as setup_server_commands
from bot.utils import refresh_all_tracked_characters, refresh_character

# Cargar variables de entorno
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Registrar el comando directamente
bot.add_command(add)
setup_lookup_commands(bot)
setup_server_commands(bot)


async def send_alerts_for_result(result):
    if result.character.level <= result.previous_level and not result.new_deaths:
        return

    settings, _ = await refresh_all_tracked_characters()
    for server_settings in settings:
        channel = bot.get_channel(int(server_settings.alert_channel_id))
        if channel is None:
            logging.error("Alert channel %s was not found.", server_settings.alert_channel_id)
            continue

        lines = []
        if result.character.level > result.previous_level:
            lines.append(
                f"{result.character.name} reached level {result.character.level} "
                f"(was {result.previous_level})."
            )
        for death in result.new_deaths:
            lines.append(f"{result.character.name} died at level {death.level} to {death.killers}.")

        await channel.send("\n".join(lines))


@tasks.loop(minutes=15)
async def tracked_character_alerts():
    _, character_ids = await refresh_all_tracked_characters()
    for character_id in character_ids:
        try:
            result = await refresh_character(character_id)
            await send_alerts_for_result(result)
        except Exception as e:
            logging.error("Error refreshing character %s: %s", character_id, e, exc_info=True)


@tracked_character_alerts.before_loop
async def before_tracked_character_alerts():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'{bot.user} se ha conectado a Discord!')
    if not tracked_character_alerts.is_running():
        tracked_character_alerts.start()
    try:
        guild_id = os.getenv('TEST_GUILD_ID')
        if guild_id:
            guild_id = int(guild_id)
            guild = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"{len(synced)} comando(s) sincronizado(s) con el servidor de prueba.")
        else:
            synced = await bot.tree.sync()
            print(f"{len(synced)} comando(s) sincronizado(s) globalmente")
    except Exception as e:
        print(f"Error al sincronizar los comandos: {e}")
        logging.error(f"Error al sincronizar los comandos: {e}", exc_info=True)

async def run_bot():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        raise ValueError("No se encontró el token. Configura la variable de entorno DISCORD_BOT_TOKEN.")
    try:
        await bot.start(token)
    except discord.errors.LoginFailure:
        print("Token inválido. Revisa tu DISCORD_BOT_TOKEN.")
        logging.error("Token inválido. Revisa tu DISCORD_BOT_TOKEN.", exc_info=True)
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")
        logging.error(f"Error al iniciar el bot: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_bot())
