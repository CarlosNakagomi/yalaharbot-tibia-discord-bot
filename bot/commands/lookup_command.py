# bot/commands/lookup_command.py
import logging
import discord
from discord.ext import commands
from asgiref.sync import sync_to_async
from bot.utils import get_character, update_or_create_character
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.tree.command()
async def lookup(ctx, character_name: str):
    """Look up a Tibia character"""
    try:
        character = await sync_to_async(get_character)(character_name)
        if character:
            other_characters = ', '.join([char.name for char in character.other_characters])
            await update_or_create_character(
                character.name, 
                character.level, 
                character.vocation, 
                character.world, 
                other_characters
            )

            embed = discord.Embed(title=f"Character: {character.name}", color=0x00ff00)
            embed.add_field(name="Level", value=character.level, inline=True)
            embed.add_field(name="Vocation", value=character.vocation, inline=True)
            embed.add_field(name="World", value=character.world, inline=True)

            if character.other_characters:
                embed.add_field(name="Other Characters", value=other_characters, inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Character '{character_name}' not found.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        logging.error(f"Error in lookup command: {str(e)}", exc_info=True)

# Añade el comando al bot
def setup(bot):
    bot.add_command(lookup)
