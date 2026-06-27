import random
import discord
from discord.ext import commands
from config_manager import config


def extract_author_id(embed: discord.Embed) -> int | None:
    """
    Extract author ID from embed footer.
    Footer format: "#channel · action · uid:1234567890"
    Falls back to None if not present (old quotes before this format).
    """
    if not embed.footer or not embed.footer.text:
        return None
    parts = embed.footer.text.split("uid:")
    if len(parts) < 2:
        return None
    try:
        return int(parts[1].strip())
    except ValueError:
        return None


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quotecount(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        count = 0
        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                author_id = extract_author_id(embed)
                if author_id == user.id:
                    count += 1
                # fallback for old quotes without uid in footer
                elif author_id is None and embed.author and embed.author.name == user.display_name:
                    count += 1

        await ctx.send(f"💬 **{user.display_name}** has been quoted **{count}** time{'s' if count != 1 else ''}.")

    @commands.command()
    async def randomquote(self, ctx, user: discord.Member = None):
        if not user:
            await ctx.send("❌ Please mention a user.", delete_after=5)
            return

        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        matches = []
        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                author_id = extract_author_id(embed)
                if author_id == user.id:
                    matches.append(msg)
                elif author_id is None and embed.author and embed.author.name == user.display_name:
                    matches.append(msg)

        if not matches:
            await ctx.send(f"❌ No quotes found from **{user.display_name}**.", delete_after=5)
            return

        msg = random.choice(matches)
        await ctx.send(embed=msg.embeds[0])


async def setup(bot):
    await bot.add_cog(Stats(bot))
