import discord
from discord.ext import commands, tasks
from config_manager import config, set_config, log_action
from .helpers import get_random_quote
from .stats import extract_author_id


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quote_of_the_day.start()

    def cog_unload(self):
        self.quote_of_the_day.cancel()

    # ── !deletequote ──────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def deletequote(self, ctx, message_id: int):
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        try:
            msg = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            await ctx.send("❌ Message not found in quoteboard.", delete_after=5)
            return

        await msg.delete()

        # remove from saved_quotes
        saved = config.get("saved_quotes", [])
        if message_id in saved:
            saved.remove(message_id)
            await set_config("saved_quotes", saved)

        await ctx.send(f"✅ Quote `{message_id}` deleted.")
        await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "deletequote", str(message_id))

    # ── !quoteleaderboard ─────────────────────────────────────

    @commands.command()
    async def quoteleaderboard(self, ctx):
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        counts: dict[str, int] = {}
        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                author = embed.author.name if embed.author else "Unknown"
                counts[author] = counts.get(author, 0) + 1

        if not counts:
            await ctx.send("❌ No quotes found.")
            return

        top5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        embed = discord.Embed(title="🏆 Quote Leaderboard", color=discord.Color.gold())
        lines = [
            f"{medals[i]} **{name}** — {count} quote{'s' if count != 1 else ''}"
            for i, (name, count) in enumerate(top5)
        ]
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    # ── !quoteoftheday ────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setqotd(self, ctx, channel: discord.TextChannel):
        """Set the channel for daily quote of the day."""
        if channel.guild.id != ctx.guild.id:
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return
        await set_config("qotd_channel", channel.id)
        await ctx.send(f"✅ Quote of the day channel set to {channel.mention}")

    @tasks.loop(hours=24)
    async def quote_of_the_day(self):
        qotd_id = config.get("qotd_channel")
        if not qotd_id:
            return

        msg = await get_random_quote(self.bot)
        if not msg:
            return

        channel = self.bot.get_channel(qotd_id)
        if channel:
            embed = msg.embeds[0].copy()
            embed.title = "📅 Quote of the Day"
            await channel.send(embed=embed)

    @quote_of_the_day.before_loop
    async def before_qotd(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Management(bot))
