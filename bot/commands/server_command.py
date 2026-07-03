import logging

import discord
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from discord.ext import commands

from bot.utils import (
    get_guild,
    get_recent_character_deaths,
    get_top_characters,
    get_watched_targets,
    get_world,
    set_alert_channel,
    unwatch_guild,
    unwatch_world,
    watch_guild,
    watch_world,
)


def require_discord_guild(ctx):
    if ctx.guild is None:
        raise ValueError("This command can only be used inside a Discord server.")


def guild_embed(tibia_guild):
    embed = discord.Embed(title=f"Guild: {tibia_guild.name}", color=0xf1c40f)
    embed.add_field(name="World", value=tibia_guild.world, inline=True)
    embed.add_field(name="Founded", value=tibia_guild.founded, inline=True)
    embed.add_field(name="Status", value="Active" if tibia_guild.active else "Inactive", inline=True)
    embed.add_field(name="Members", value=len(tibia_guild.members), inline=True)
    embed.add_field(name="Applications", value="Open" if tibia_guild.open_applications else "Closed", inline=True)
    if tibia_guild.description:
        embed.description = tibia_guild.description[:400]
    return embed


def online_embed(world):
    players = sorted(world.online_players, key=lambda player: player.level, reverse=True)
    embed = discord.Embed(title=f"Online on {world.name}", color=0x2ecc71)
    embed.description = f"{len(players)} players online. Record: {world.record_count}."

    for player in players[:15]:
        embed.add_field(
            name=player.name,
            value=f"Level {player.level} {player.vocation}",
            inline=False,
        )
    return embed


@commands.hybrid_command(name="setalerts")
@commands.has_guild_permissions(manage_guild=True)
async def setalerts(ctx, channel: discord.TextChannel):
    """Set the channel used for automatic Tibia alerts"""
    try:
        require_discord_guild(ctx)
        await set_alert_channel(ctx.guild.id, channel.id)
        await ctx.send(f"Alerts will be posted in {channel.mention}.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in setalerts command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="watchworld")
@commands.has_guild_permissions(manage_guild=True)
async def watchworld(ctx, world_name: str):
    """Watch a Tibia world for this Discord server"""
    try:
        require_discord_guild(ctx)
        await watch_world(ctx.guild.id, world_name)
        await ctx.send(f"Watching world: {world_name}.", ephemeral=True)
    except ObjectDoesNotExist:
        await ctx.send("Set an alert channel first with `/setalerts #channel`.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in watchworld command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="unwatchworld")
@commands.has_guild_permissions(manage_guild=True)
async def unwatchworld(ctx, world_name: str):
    """Stop watching a Tibia world for this Discord server"""
    try:
        require_discord_guild(ctx)
        deleted = await unwatch_world(ctx.guild.id, world_name)
        message = f"Stopped watching world: {world_name}." if deleted else f"{world_name} was not watched."
        await ctx.send(message, ephemeral=True)
    except ObjectDoesNotExist:
        await ctx.send("Set an alert channel first with `/setalerts #channel`.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in unwatchworld command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="watchguild")
@commands.has_guild_permissions(manage_guild=True)
async def watchguild(ctx, guild_name: str):
    """Watch a Tibia guild for this Discord server"""
    try:
        require_discord_guild(ctx)
        await watch_guild(ctx.guild.id, guild_name)
        await ctx.send(f"Watching guild: {guild_name}.", ephemeral=True)
    except ObjectDoesNotExist:
        await ctx.send("Set an alert channel first with `/setalerts #channel`.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in watchguild command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="unwatchguild")
@commands.has_guild_permissions(manage_guild=True)
async def unwatchguild(ctx, guild_name: str):
    """Stop watching a Tibia guild for this Discord server"""
    try:
        require_discord_guild(ctx)
        deleted = await unwatch_guild(ctx.guild.id, guild_name)
        message = f"Stopped watching guild: {guild_name}." if deleted else f"{guild_name} was not watched."
        await ctx.send(message, ephemeral=True)
    except ObjectDoesNotExist:
        await ctx.send("Set an alert channel first with `/setalerts #channel`.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in unwatchguild command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="watched")
async def watched(ctx):
    """Show watched Tibia worlds and guilds for this Discord server"""
    try:
        require_discord_guild(ctx)
        settings, worlds, guilds = await get_watched_targets(ctx.guild.id)
        channel = ctx.guild.get_channel(int(settings.alert_channel_id))
        embed = discord.Embed(title="Watched Tibia targets", color=0x95a5a6)
        embed.add_field(name="Alert channel", value=channel.mention if channel else settings.alert_channel_id, inline=False)
        embed.add_field(name="Worlds", value=", ".join(worlds) if worlds else "None", inline=False)
        embed.add_field(name="Guilds", value=", ".join(guilds) if guilds else "None", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
    except ObjectDoesNotExist:
        await ctx.send("No alert settings yet. Use `/setalerts #channel`.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in watched command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="online")
async def online(ctx, world_name: str):
    """Show current online players for a Tibia world"""
    try:
        world = await sync_to_async(get_world)(world_name)
        if world is None:
            await ctx.send(f"World '{world_name}' not found.", ephemeral=True)
            return
        await ctx.send(embed=online_embed(world))
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in online command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="guild")
async def guild(ctx, guild_name: str):
    """Look up a Tibia guild"""
    try:
        tibia_guild = await sync_to_async(get_guild)(guild_name)
        if tibia_guild is None:
            await ctx.send(f"Guild '{guild_name}' not found.", ephemeral=True)
            return
        await ctx.send(embed=guild_embed(tibia_guild))
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in guild command: {str(e)}", exc_info=True)


@commands.hybrid_command(name="leaderboard")
async def leaderboard(ctx):
    """Show tracked character leaderboards"""
    try:
        characters = await get_top_characters()
        recent_deaths = await get_recent_character_deaths()

        embed = discord.Embed(title="YalaharBot Leaderboard", color=0x1abc9c)
        embed.add_field(
            name="Highest tracked levels",
            value="\n".join(
                f"{index}. {character.name} - {character.level} {character.vocation}"
                for index, character in enumerate(characters, start=1)
            ) if characters else "No tracked characters yet.",
            inline=False,
        )
        embed.add_field(
            name="Recent deaths",
            value="\n".join(
                f"{death.character.name} at {death.level} to {death.killers}"
                for death in recent_deaths[:5]
            ) if recent_deaths else "No remembered deaths yet.",
            inline=False,
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in leaderboard command: {str(e)}", exc_info=True)


def setup(bot):
    bot.add_command(setalerts)
    bot.add_command(watchworld)
    bot.add_command(unwatchworld)
    bot.add_command(watchguild)
    bot.add_command(unwatchguild)
    bot.add_command(watched)
    bot.add_command(online)
    bot.add_command(guild)
    bot.add_command(leaderboard)
