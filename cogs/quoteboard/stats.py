import random
import discord
from discord.ext import commands
from utils import load_config


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quotecount(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        config = load_config()
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.")
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.")
            return

        count = 0
        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                if embed.author and embed.author.name == user.display_name:
                    count += 1

        await ctx.send(f"💬 **{user.display_name}** has been quoted **{count}** time{'s' if count != 1 else ''}.")

    @commands.command()
    async def randomquote(self, ctx, user: discord.Member = None):
        if not user:
            await ctx.send("❌ Please mention a user.")
            return

        config = load_config()
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.")
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.")
            return

        matches = [
            msg async for msg in channel.history(limit=500)
            if msg.author.bot and msg.embeds
            and msg.embeds[0].author
            and msg.embeds[0].author.name == user.display_name
        ]

        if not matches:
            await ctx.send(f"❌ No quotes found from **{user.display_name}**.")
            return

        msg = random.choice(matches)
        await ctx.send(embed=msg.embeds[0])
