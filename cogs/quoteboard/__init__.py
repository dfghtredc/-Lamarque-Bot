from .setup import Setup
from .core import Core
from .pinned import Pinned
from .stats import Stats
from .feed import Feed
from .management import Management

async def setup(bot):
    await bot.add_cog(Setup(bot))
    await bot.add_cog(Core(bot))
    await bot.add_cog(Pinned(bot))
    await bot.add_cog(Stats(bot))
    await bot.add_cog(Feed(bot))
    await bot.add_cog(Management(bot))
