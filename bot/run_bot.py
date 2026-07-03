import os
import sys
import asyncio
import logging
import discord
from discord.ext import commands
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

# Cargar variables de entorno
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Registrar el comando directamente
bot.add_command(add)

@bot.event
async def on_ready():
    print(f'{bot.user} se ha conectado a Discord!')
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
