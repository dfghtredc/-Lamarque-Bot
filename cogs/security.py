import time
import discord
from discord.ext import commands
from collections import defaultdict

# ── Rate limiter ─────────────────────────────────────────────
# Per-user, per-command cooldown tracker
# Stored in memory — resets on bot restart (intentional)

class RateLimiter:
    def __init__(self):
        self._calls: dict[tuple, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int, command: str, max_calls: int, window: float) -> bool:
        key = (user_id, command)
        now = time.monotonic()
        # prune old calls outside the window
        self._calls[key] = [t for t in self._calls[key] if now - t < window]
        if len(self._calls[key]) >= max_calls:
            return False
        self._calls[key].append(now)
        return True

    def time_remaining(self, user_id: int, command: str, window: float) -> float:
        key = (user_id, command)
        now = time.monotonic()
        if not self._calls[key]:
            return 0.0
        oldest = min(self._calls[key])
        return max(0.0, window - (now - oldest))


# Global rate limiter instance — imported by all cogs
rate_limiter = RateLimiter()

# ── Rate limit config ─────────────────────────────────────────
LIMITS = {
    "pull":      {"max_calls": 3,  "window": 60.0},   # 3 pulls per minute
    "pullid":    {"max_calls": 3,  "window": 60.0},
    "pullmsg":   {"max_calls": 5,  "window": 60.0},
    "savequote": {"max_calls": 5,  "window": 60.0},
    "quote":     {"max_calls": 10, "window": 60.0},
    "lockdown":  {"max_calls": 5,  "window": 60.0},
}

# ── Input validators ──────────────────────────────────────────

def validate_guild_channel(channel: discord.TextChannel, guild: discord.Guild) -> bool:
    """Ensure a channel belongs to the current guild — prevents cross-guild leakage."""
    return channel.guild.id == guild.id

def validate_guild_member(member: discord.Member, guild: discord.Guild) -> bool:
    """Ensure a member belongs to the current guild."""
    return member.guild.id == guild.id

def validate_message_id(message_id: int) -> bool:
    """Basic snowflake ID sanity check — Discord IDs are 17-19 digits."""
    return 10**16 <= message_id <= 10**19

def validate_user_id(user_id: int) -> bool:
    """Basic snowflake ID sanity check."""
    return 10**16 <= user_id <= 10**19

# ── Permission check ──────────────────────────────────────────

def can_use_command(member: discord.Member, config: dict) -> bool:
    """
    Unified permission check used by both prefix and slash commands.
    If quotesave_role is set — member must have it.
    If not set — everyone can use it.
    Admins always bypass.
    """
    if member.guild_permissions.administrator:
        return True
    role_id = config.get("quotesave_role")
    if not role_id:
        return True
    return any(r.id == role_id for r in member.roles)

# ── Security cog ─────────────────────────────────────────────
# Handles global error responses for rate limit violations
# and registers a global check that runs before every command

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_check(self.global_rate_check)

    def cog_unload(self):
        self.bot.remove_check(self.global_rate_check)

    async def global_rate_check(self, ctx: commands.Context) -> bool:
        """Global check — runs before every prefix command."""
        command_name = ctx.command.name if ctx.command else None
        if command_name not in LIMITS:
            return True  # no limit defined for this command

        cfg = LIMITS[command_name]
        allowed = rate_limiter.is_allowed(
            ctx.author.id, command_name, cfg["max_calls"], cfg["window"]
        )
        if not allowed:
            remaining = rate_limiter.time_remaining(
                ctx.author.id, command_name, cfg["window"]
            )
            await ctx.send(
                f"⏳ Slow down. You can use `!{command_name}` again in "
                f"**{remaining:.1f}s**.",
                delete_after=5
            )
            return False
        return True

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Central error handler — catches permission errors, bad args, etc."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}", delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            pass  # ignore silently
        elif isinstance(error, commands.CheckFailure):
            pass  # rate limiter already sent a message
        else:
            # log unexpected errors without exposing internals to users
            print(f"[ERROR] {ctx.command}: {error}")
            await ctx.send("❌ Something went wrong. Try again.", delete_after=5)


async def setup(bot):
    await bot.add_cog(Security(bot))
