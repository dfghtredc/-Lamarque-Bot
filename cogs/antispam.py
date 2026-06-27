import time
import discord
from discord.ext import commands
from collections import defaultdict
from config_manager import config, set_config
from cogs.security import alert_owner

# per-user message timestamps — in memory
_message_times: dict[tuple[int, int], list[float]] = defaultdict(list)

SPAM_THRESHOLD = 5    # messages
SPAM_WINDOW    = 5.0  # seconds


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setspam(self, ctx, threshold: int, window: int):
        """Set spam threshold. !setspam 5 5 = 5 messages in 5 seconds."""
        await set_config("spam_threshold", threshold)
        await set_config("spam_window", window)
        await ctx.send(f"✅ Spam threshold set: {threshold} messages in {window} seconds.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.author.guild_permissions.administrator:
            return

        threshold = config.get("spam_threshold", SPAM_THRESHOLD)
        window = float(config.get("spam_window", SPAM_WINDOW))

        key = (message.author.id, message.guild.id)
        now = time.monotonic()

        # prune old timestamps
        _message_times[key] = [t for t in _message_times[key] if now - t < window]
        _message_times[key].append(now)

        if len(_message_times[key]) >= threshold:
            muted_role = discord.utils.get(message.guild.roles, name="Muted")
            if muted_role and muted_role not in message.author.roles:
                try:
                    await message.author.add_roles(muted_role, reason="Anti-spam auto-mute")
                    _message_times[key] = []

                    # notify in channel
                    log_channel_id = config.get("log_channel")
                    if log_channel_id:
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel:
                            embed = discord.Embed(
                                description=f"🔇 **{message.author.display_name}** was auto-muted for spamming.",
                                color=discord.Color.red()
                            )
                            await log_channel.send(embed=embed)

                    # alert owner
                    await alert_owner(
                        self.bot,
                        f"🔇 Anti-spam triggered\n"
                        f"User: {message.author} (`{message.author.id}`)\n"
                        f"Server: {message.guild.name}\n"
                        f"Messages: {threshold} in {window}s"
                    )
                except discord.Forbidden:
                    pass


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
