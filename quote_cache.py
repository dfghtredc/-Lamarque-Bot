"""
quote_cache.py
--------------
In-memory cache of quoteboard messages.
Eliminates repeated Discord API history fetches.

TTL: 10 minutes — cache refreshes automatically.
Invalidated manually when a new quote is saved.

Usage:
    from quote_cache import quote_cache
    msg = await quote_cache.get_random(bot)
    await quote_cache.invalidate()
"""

import random
import time
import discord

CACHE_TTL = 600  # 10 minutes


class QuoteCache:
    def __init__(self):
        self._messages: list = []
        self._last_refresh: float = 0.0
        self._board_id: int | None = None

    def _is_stale(self) -> bool:
        return time.monotonic() - self._last_refresh > CACHE_TTL

    async def _refresh(self, bot, board_id: int) -> None:
        channel = bot.get_channel(board_id)
        if not channel:
            self._messages = []
            return
        self._messages = [
            msg async for msg in channel.history(limit=300)
            if msg.author.bot and msg.embeds
        ]
        self._last_refresh = time.monotonic()
        self._board_id = board_id

    async def get_random(self, bot, board_id: int, pinned_names: list[str] | None = None):
        """
        Return a random quote message.
        If pinned_names provided, prioritize quotes from those users.
        Refreshes cache if stale or board changed.
        """
        if self._is_stale() or self._board_id != board_id:
            await self._refresh(bot, board_id)

        if not self._messages:
            return None

        if pinned_names:
            pinned_msgs = [
                msg for msg in self._messages
                if msg.embeds[0].author
                and any(name in msg.embeds[0].author.name for name in pinned_names)
            ]
            if pinned_msgs:
                return random.choice(pinned_msgs)

        return random.choice(self._messages)

    async def invalidate(self) -> None:
        """Call this after saving a new quote so the cache reflects it."""
        self._last_refresh = 0.0


# Global instance — imported by helpers and feed
quote_cache = QuoteCache()
