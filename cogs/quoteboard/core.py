import random
import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config
from .helpers import can_save_quote, save_to_quoteboard, get_random_quote


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def savequote(self, ctx):
        config = load_config()

        if not can_save_quote(ctx.author, config):
            await ctx.send("❌ You don't have permission to save quotes.")
            return

        if not ctx.message.reference:
            await ctx.send("❌ Reply to a message to save it.")
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.")
            return

        try:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.send("❌ Couldn't find that message.")
            return

        result = await save_to_quoteboard(self.bot, msg, ctx.channel, f"saved by {ctx.author.display_name}")
        if not result:
            await ctx.send("❌ Already saved or quoteboard unavailable.")
            return

        await ctx.message.delete()

    @commands.command()
    async def pull(self, ctx, user: discord.Member, channel: discord.TextChannel = None):
        config = load_config()

        if not can_save_quote(ctx.author, config):
            await ctx.send("❌ You don't have permission to pull quotes.")
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.")
            return

        search_channel = channel or ctx.channel
        messages = [
            msg async for msg in search_channel.history(limit=500)
            if msg.author.id == user.id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await ctx.send(f"❌ No messages found from {user.display_name} in {search_channel.mention}.")
            return

        saved = config.get("saved_quotes", [])
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await ctx.send(f"❌ All messages from {user.display_name} have already been saved.")
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if result:
            await ctx.send(f"✅ Pulled a quote from {user.display_name} into the quoteboard.")

    @commands.command()
    async def pullid(self, ctx, user_id: int, channel: discord.TextChannel = None):
        config = load_config()

        if not can_save_quote(ctx.author, config):
            await ctx.send("❌ You don't have permission to pull quotes.")
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.")
            return

        search_channel = channel or ctx.channel
        messages = [
            msg async for msg in search_channel.history(limit=500)
            if msg.author.id == user_id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await ctx.send(f"❌ No messages found from user `{user_id}` in {search_channel.mention}.")
            return

        saved = config.get("saved_quotes", [])
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await ctx.send(f"❌ All messages from user `{user_id}` have already been saved.")
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if result:
            await ctx.send(f"✅ Pulled a quote from user `{user_id}` into the quoteboard.")

    @commands.command()
    async def pullmsg(self, ctx, message_id: int, channel: discord.TextChannel = None):
        config = load_config()

        if not can_save_quote(ctx.author, config):
            await ctx.send("❌ You don't have permission to pull quotes.")
            return

        if not config.get("quoteboard_channel"):
            await ctx.send("❌ No quoteboard channel set.")
            return

        search_channel = channel or ctx.channel

        try:
            msg = await search_channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found. Try `!pullmsg <id> #channel`.")
            return

        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {ctx.author.display_name}")
        if not result:
            await ctx.send("❌ Already saved or quoteboard unavailable.")
            return

        await ctx.send(f"✅ Saved message from **{msg.author.display_name}** into the quoteboard.")

    @commands.command()
    async def quote(self, ctx):
        msg = await get_random_quote(self.bot)
        if not msg:
            await ctx.send("❌ No quotes saved yet.")
            return
        await ctx.send(embed=msg.embeds[0])

    # ── slash commands ────────────────────────────────────────

    @app_commands.command(name="quote", description="Post a random saved quote")
    async def slash_quote(self, interaction: discord.Interaction):
        msg = await get_random_quote(self.bot)
        if not msg:
            await interaction.response.send_message("❌ No quotes saved yet.")
            return
        await interaction.response.send_message(embed=msg.embeds[0])

    @app_commands.command(name="pull", description="Pull a random message from a user into the quoteboard")
    @app_commands.describe(user="The user to pull from", channel="Optional channel to search in")
    async def slash_pull(self, interaction: discord.Interaction, user: discord.Member, channel: discord.TextChannel = None):
        config = load_config()
        if not can_save_quote(interaction.user, config):
            await interaction.response.send_message("❌ You don't have permission.")
            return

        if not config.get("quoteboard_channel"):
            await interaction.response.send_message("❌ No quoteboard channel set.")
            return

        await interaction.response.defer()

        search_channel = channel or interaction.channel
        messages = [
            msg async for msg in search_channel.history(limit=500)
            if msg.author.id == user.id and msg.content and not msg.content.startswith("!")
        ]

        if not messages:
            await interaction.followup.send(f"❌ No messages found from {user.display_name}.")
            return

        saved = config.get("saved_quotes", [])
        unsaved = [msg for msg in messages if msg.id not in saved]

        if not unsaved:
            await interaction.followup.send(f"❌ All messages from {user.display_name} already saved.")
            return

        msg = random.choice(unsaved)
        result = await save_to_quoteboard(self.bot, msg, search_channel, f"pulled by {interaction.user.display_name}")
        if result:
            await interaction.followup.send(f"✅ Pulled a quote from {user.display_name}.")
