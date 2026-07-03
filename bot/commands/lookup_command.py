import logging
import discord
from discord.ext import commands
from asgiref.sync import sync_to_async
from bot.utils import (
    get_character,
    get_linked_characters,
    get_recent_deaths,
    other_character_names,
    refresh_character,
    save_tibia_character,
)


def character_embed(character):
    embed = discord.Embed(title=f"Character: {character.name}", color=0x00ff00)
    embed.add_field(name="Level", value=character.level, inline=True)
    embed.add_field(name="Vocation", value=character.vocation, inline=True)
    embed.add_field(name="World", value=character.world, inline=True)

    other_characters = other_character_names(character)
    if other_characters:
        embed.add_field(name="Other Characters", value=other_characters, inline=False)

    return embed


def linked_characters_embed(user, characters):
    embed = discord.Embed(title=f"{user.display_name}'s Tibia characters", color=0x3498db)
    for character in characters:
        embed.add_field(
            name=character.name,
            value=f"Level {character.level} {character.vocation} on {character.world}",
            inline=False,
        )
    return embed


def death_line(death):
    return f"Level {death.level} on {death.died_at:%Y-%m-%d}: {death.killers}"


@commands.hybrid_command(name="lookup")
async def lookup(ctx, character_name: str):
    """Look up a Tibia character"""
    try:
        character = await sync_to_async(get_character)(character_name)
        if character:
            await save_tibia_character(character)
            await ctx.send(embed=character_embed(character))
        else:
            await ctx.send(f"Character '{character_name}' not found.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        logging.error(f"Error in lookup command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="mychars")
async def mychars(ctx):
    """Show the Tibia characters linked to your Discord account"""
    try:
        characters = await get_linked_characters(ctx.author.id)
        if not characters:
            await ctx.send("You have no linked Tibia characters yet. Use `/add character_name` first.", ephemeral=True)
            return

        await ctx.send(embed=linked_characters_embed(ctx.author, characters), ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in mychars command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="whois")
async def whois(ctx, user: discord.Member):
    """Show the Tibia characters linked to a Discord user"""
    try:
        characters = await get_linked_characters(user.id)
        if not characters:
            await ctx.send(f"{user.display_name} has no linked Tibia characters yet.", ephemeral=True)
            return

        await ctx.send(embed=linked_characters_embed(user, characters), ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in whois command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="refresh")
async def refresh(ctx):
    """Refresh your linked Tibia characters and report level/death changes"""
    try:
        characters = await get_linked_characters(ctx.author.id)
        if not characters:
            await ctx.send("You have no linked Tibia characters yet. Use `/add character_name` first.", ephemeral=True)
            return

        lines = []
        for character in characters:
            result = await refresh_character(character.id)
            if result.character.level > result.previous_level:
                lines.append(
                    f"{result.character.name} reached level {result.character.level} "
                    f"(was {result.previous_level})."
                )
            else:
                lines.append(f"{result.character.name} is still level {result.character.level}.")

            for death in result.new_deaths:
                lines.append(f"{result.character.name} died at level {death.level} to {death.killers}.")

        await ctx.send("\n".join(lines), ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in refresh command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="deaths")
async def deaths(ctx, character_name: str):
    """Show recent remembered deaths for a tracked Tibia character"""
    try:
        character = await sync_to_async(get_character)(character_name)
        if character is None:
            await ctx.send(f"Character '{character_name}' not found.", ephemeral=True)
            return

        await save_tibia_character(character)
        recent_deaths = await get_recent_deaths(character.name)
        if not recent_deaths:
            await ctx.send(f"No remembered deaths for {character.name}.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Recent deaths: {character.name}", color=0xe74c3c)
        embed.description = "\n".join(death_line(death) for death in recent_deaths)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in deaths command: {str(e)}", exc_info=True)


def setup(bot):
    bot.add_command(lookup)
    bot.add_command(mychars)
    bot.add_command(whois)
    bot.add_command(refresh)
    bot.add_command(deaths)
