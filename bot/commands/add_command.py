import logging
import discord
from discord.ext import commands
from asgiref.sync import sync_to_async
from bot.utils import get_character, add_character_to_discord_user

@commands.hybrid_command()
async def add(ctx: commands.Context, character_name: str):
    """Add Tibia character(s) to your Discord account"""
    try:
        character = await sync_to_async(get_character)(character_name)
        if character:
            all_characters = [character.name] + [char.name for char in character.other_characters]
            unique_characters = list(dict.fromkeys(all_characters))
            view = CharacterSelectView(unique_characters)
            await ctx.send(
                f"Select which character(s) from the account of {character_name} you want to add:",
                view=view,
                ephemeral=True
            )
        else:
            await ctx.send(f"Character '{character_name}' not found.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}", ephemeral=True)
        logging.error(f"Error in add command: {str(e)}", exc_info=True)

class CharacterSelect(discord.ui.Select):
    def __init__(self, characters):
        options = [
            discord.SelectOption(label=char, value=char)
            for char in characters
        ]
        super().__init__(placeholder="Select characters to add", options=options, min_values=1, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        added_chars = []

        try:
            for char_name in self.values:
                discord_user, character = await add_character_to_discord_user(user_id, char_name)
                added_chars.append(character.name)
            
            await interaction.response.send_message(f"Added characters to your account: {', '.join(added_chars)}", ephemeral=True)
            logging.info(f"Added characters {added_chars} to Discord user ID {user_id}")
        except Exception as e:
            logging.error(f"Error adding characters: {str(e)}", exc_info=True)
            await interaction.response.send_message(f"An error occurred while adding characters: {str(e)}", ephemeral=True)

class CharacterSelectView(discord.ui.View):
    def __init__(self, characters):
        super().__init__()
        self.add_item(CharacterSelect(characters))
