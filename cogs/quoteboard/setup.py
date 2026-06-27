import discord
from discord.ext import commands
from utils import load_config, save_config


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquoteboard(self, ctx, channel: discord.TextChannel):
        config = load_config()
        config["quoteboard_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Quoteboard set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setechofeed(self, ctx, channel: discord.TextChannel):
        config = load_config()
        config["echo_feed_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Echo feed set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquoterole(self, ctx, role: discord.Role):
        config = load_config()
        config["quotesave_role"] = role.id
        save_config(config)
        await ctx.send(f"✅ Quote save role set to {role.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquotestream(self, ctx, minutes: int):
        if minutes < 1:
            await ctx.send("❌ Minimum is 1 minute.")
            return
        config = load_config()
        config["quote_interval"] = minutes
        save_config(config)
        await ctx.send(f"✅ Quote feed interval set to {minutes} minutes.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quotestop(self, ctx):
        cog = self.bot.cogs.get("Feed")
        if not cog:
            await ctx.send("❌ Feed cog not found.")
            return
        cog.quote_feed.stop()
        await ctx.send("⏹️ Quote feed stopped.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quotestart(self, ctx):
        cog = self.bot.cogs.get("Feed")
        if not cog:
            await ctx.send("❌ Feed cog not found.")
            return
        cog.quote_feed.start()
        await ctx.send("▶️ Quote feed started.")