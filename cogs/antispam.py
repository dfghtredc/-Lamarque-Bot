import time
import discord
from discord.ext import commands
from collections import defaultdict
from datetime import timedelta
from config_manager import config, set_config
from cogs.security import alert_owner

_message_times: dict[tuple[int, int], list[float]] = defaultdict(list)

SPAM_THRESHOLD = 5
SPAM_WINDOW    = 5.0
TIMEOUT_DURATION = 300  # 5 minutes default


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setspam(self, ctx, threshold: int, window: int, timeout_minutes: int = 5):
        """
        Set spam threshold.
        !setspam 5 5 10 = 5 messages in 5 seconds → 10 minute timeout
        """
        await set_config("spam_threshold", threshold)
        await set_config("spam_window", window)
        await set_config("spam_timeout", timeout_minutes * 60)
        await ctx.send(
            f"✅ Spam threshold: **{threshold}** messages in **{window}s** "
            f"→ **{timeout_minutes} minute** timeout."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.author.guild_permissions.administrator:
            return
        # skip if already timed out
        if message.author.is_timed_out():
            return

        threshold = config.get("spam_threshold", SPAM_THRESHOLD)
        window = float(config.get("spam_window", SPAM_WINDOW))
        timeout_seconds = int(config.get("spam_timeout", TIMEOUT_DURATION))

        key = (message.author.id, message.guild.id)
        now = time.monotonic()

        _message_times[key] = [t for t in _message_times[key] if now - t < window]
        _message_times[key].append(now)

        if len(_message_times[key]) >= threshold:
            try:
                # native Discord timeout — no role needed
                await message.author.timeout(
                    timedelta(seconds=timeout_seconds),
                    reason=f"Auto-timeout: {threshold} messages in {window}s"
                )
                _message_times[key] = []

                log_channel_id = config.get("log_channel")
                if log_channel_id:
                    log_channel = message.guild.get_channel(log_channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            description=(
                                f"⏱️ **{message.author.mention}** was timed out for "
                                f"**{timeout_seconds // 60} minutes** for spamming."
                            ),
                            color=discord.Color.red()
                        )
                        embed.set_thumbnail(url=message.author.display_avatar.url)
                        await log_channel.send(embed=embed)

                await alert_owner(
                    self.bot,
                    f"⏱️ Anti-spam timeout\n"
                    f"User: {message.author} (`{message.author.id}`)\n"
                    f"Server: {message.guild.name}\n"
                    f"Duration: {timeout_seconds // 60} minutes\n"
                    f"Trigger: {threshold} messages in {window}s"
                )
            except discord.Forbidden:
                # fallback to Muted role if bot lacks timeout permission
                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if muted_role and muted_role not in message.author.roles:
                    try:
                        await message.author.add_roles(muted_role, reason="Anti-spam fallback")
                        _message_times[key] = []
                    except discord.Forbidden:
                        pass


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
