import random
import discord
from discord import app_commands
from discord.ext import commands
from config_manager import config
from cogs.security import can_use_command, validate_guild_channel, validate_message_id, validate_user_id
from .helpers import save_to_quoteboard, get_random_quote


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── savequote ─────────────────────────────────────────────

    @commands.command()
    async def savequote(self, ctx):
        if not can_use_command(ctx.author, config):
            await ctx.send("❌ You don't have permission.", delete_after=5)
            return

        if not ctx.message.reference:
            await ctx.send("❌ Reply to a message to save it.", delete_after=5)
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        try:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except (discord.NotFound, discord.HTTPException):
            await ctx.send("❌ Couldn't find that message.", delete_after=5)
            return

        result = await save_to_quoteboard(self.bot, msg, ctx.channel, f"saved by {ctx.author.display_name}")
        if not result:
            await ctx.send("❌ Already saved or quoteboard unavailable.", delete_after=5)
            return

        await ctx.message.delete()

    # ── pull ──────────────────────────────────────────────────

    @commands.command()
    async def pull(self, ctx, user: discord.Member, channel: discord.TextChannel = None):
        if not can_use_command(ctx.author, config):
            await ctx.send("❌ You don't have permission.", delete_after=5)
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        search_channel = channel or ctx.channel

        # guild scope check
        if not validate_guild_channel(search_channel, ctx.guild):
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return

        if not validate_guild_channel(discord.utils.get(ctx.guild.text_channels, id=search_channel.id) or search_channel, ctx.guild):
            await ctx.send("❌ Invalid channel.", delete_after=5)
            return

        messages = [
            msg async for msg in search_channel.history(limit=200)
            if msg.author.id == user.id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await ctx.send(f"❌ No messages found from {user.display_name}.", delete_after=5)
            return

        saved = set(config.get("saved_quotes", []))
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await ctx.send(f"❌ All messages from {user.display_name} already saved.", delete_after=5)
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if result:
            await ctx.send(f"✅ Pulled a quote from {user.display_name}.")

    # ── pullid ────────────────────────────────────────────────

    @commands.command()
    async def pullid(self, ctx, user_id: int, channel: discord.TextChannel = None):
        if not can_use_command(ctx.author, config):
            await ctx.send("❌ You don't have permission.", delete_after=5)
            return

        if not validate_user_id(user_id):
            await ctx.send("❌ Invalid user ID.", delete_after=5)
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        search_channel = channel or ctx.channel

        if not validate_guild_channel(search_channel, ctx.guild):
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return

        messages = [
            msg async for msg in search_channel.history(limit=200)
            if msg.author.id == user_id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await ctx.send(f"❌ No messages found from user `{user_id}`.", delete_after=5)
            return

        saved = set(config.get("saved_quotes", []))
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await ctx.send(f"❌ All messages from user `{user_id}` already saved.", delete_after=5)
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if result:
            await ctx.send(f"✅ Pulled a quote from user `{user_id}`.")

    # ── pullmsg ───────────────────────────────────────────────

    @commands.command()
    async def pullmsg(self, ctx, message_id: int, channel: discord.TextChannel = None):
        if not can_use_command(ctx.author, config):
            await ctx.send("❌ You don't have permission.", delete_after=5)
            return

        if not validate_message_id(message_id):
            await ctx.send("❌ Invalid message ID.", delete_after=5)
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        search_channel = channel or ctx.channel

        if not validate_guild_channel(search_channel, ctx.guild):
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return

        try:
            msg = await search_channel.fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            await ctx.send("❌ Message not found. Try `!pullmsg <id> #channel`.", delete_after=5)
            return

        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if not result:
            await ctx.send("❌ Already saved or quoteboard unavailable.", delete_after=5)
            return

        await ctx.send(f"✅ Saved message from **{msg.author.display_name}**.")

    # ── quote ─────────────────────────────────────────────────

    @commands.command()
    async def quote(self, ctx):
        msg = await get_random_quote(self.bot)
        if not msg:
            await ctx.send("❌ No quotes saved yet.", delete_after=5)
            return
        await ctx.send(embed=msg.embeds[0])

    # ── slash commands ────────────────────────────────────────

    @app_commands.command(name="quote", description="Post a random saved quote")
    async def slash_quote(self, interaction: discord.Interaction):
        msg = await get_random_quote(self.bot)
        if not msg:
            await interaction.response.send_message("❌ No quotes saved yet.", ephemeral=True)
            return
        await interaction.response.send_message(embed=msg.embeds[0])

    @app_commands.command(name="pull", description="Pull a random message from a user into the quoteboard")
    @app_commands.describe(user="The user to pull from", channel="Optional channel to search in")
    async def slash_pull(self, interaction: discord.Interaction, user: discord.Member, channel: discord.TextChannel = None):
        if not can_use_command(interaction.user, config):
            await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
            return

        if not config.get("quoteboard_channel"):
            await interaction.response.send_message("❌ No quoteboard channel set.", ephemeral=True)
            return

        search_channel = channel or interaction.channel

        if not validate_guild_channel(search_channel, interaction.guild):
            await interaction.response.send_message("❌ That channel isn't in this server.", ephemeral=True)
            return

        await interaction.response.defer()

        messages = [
            msg async for msg in search_channel.history(limit=200)
            if msg.author.id == user.id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await interaction.followup.send(f"❌ No messages found from {user.display_name}.")
            return

        saved = set(config.get("saved_quotes", []))
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await interaction.followup.send(f"❌ All messages from {user.display_name} already saved.")
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {interaction.user.display_name}")
        if result:
            await interaction.followup.send(f"✅ Pulled a quote from {user.display_name}.")


async def setup(bot):
    await bot.add_cog(Core(bot))
