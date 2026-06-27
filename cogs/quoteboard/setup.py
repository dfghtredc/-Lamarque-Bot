import discord
from discord.ext import commands
from config_manager import config, save_config


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquoteboard(self, ctx, channel: discord.TextChannel):
        if channel.guild.id != ctx.guild.id:
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return
        config["quoteboard_channel"] = channel.id
        save_config()
        await ctx.send(f"✅ Quoteboard set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setechofeed(self, ctx, channel: discord.TextChannel):
        if channel.guild.id != ctx.guild.id:
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return
        config["echo_feed_channel"] = channel.id
        save_config()
        await ctx.send(f"✅ Echo feed set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquoterole(self, ctx, role: discord.Role):
        config["quotesave_role"] = role.id
        save_config()
        await ctx.send(f"✅ Quote save role set to {role.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setquotestream(self, ctx, minutes: int):
        if minutes < 1:
            await ctx.send("❌ Minimum is 1 minute.", delete_after=5)
            return
        config["quote_interval"] = minutes
        save_config()
        # update the live feed loop interval
        feed_cog = self.bot.cogs.get("Feed")
        if feed_cog:
            feed_cog.quote_feed.change_interval(minutes=minutes)
        await ctx.send(f"✅ Quote feed interval set to {minutes} minutes.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quotestop(self, ctx):
        feed_cog = self.bot.cogs.get("Feed")
        if not feed_cog:
            await ctx.send("❌ Feed cog not found.", delete_after=5)
            return
        feed_cog.quote_feed.stop()
        await ctx.send("⏹️ Quote feed stopped.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quotestart(self, ctx):
        feed_cog = self.bot.cogs.get("Feed")
        if not feed_cog:
            await ctx.send("❌ Feed cog not found.", delete_after=5)
            return
        feed_cog.quote_feed.start()
        await ctx.send("▶️ Quote feed started.")


async def setup(bot):
    await bot.add_cog(Setup(bot))
