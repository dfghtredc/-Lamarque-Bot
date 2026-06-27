from discord.ext import commands, tasks
from config_manager import config
from .helpers import get_random_quote


class Feed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # read stored interval — default 30 if not set
        interval = config.get("quote_interval", 30)
        self.quote_feed.change_interval(minutes=interval)
        self.quote_feed.start()

    def cog_unload(self):
        self.quote_feed.cancel()

    @tasks.loop(minutes=30)
    async def quote_feed(self):
        feed_id = config.get("echo_feed_channel")
        if not feed_id:
            return

        msg = await get_random_quote(self.bot, prioritize_pinned=True)
        if not msg:
            return

        channel = self.bot.get_channel(feed_id)
        if channel:
            await channel.send(embed=msg.embeds[0])

    @quote_feed.before_loop
    async def before_quote_feed(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Feed(bot))
