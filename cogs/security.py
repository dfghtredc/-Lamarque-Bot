import time
import discord
from discord.ext import commands
from collections import defaultdict
from config_manager import (
    config, log_action,
    is_allowlisted, add_to_allowlist, remove_from_allowlist, get_allowlist
)

# ── Rate limiter ──────────────────────────────────────────────

class RateLimiter:
    def __init__(self):
        self._calls: dict[tuple, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int, command: str, max_calls: int, window: float) -> bool:
        key = (user_id, command)
        now = time.monotonic()
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


rate_limiter = RateLimiter()

LIMITS = {
    "pull":      {"max_calls": 3,  "window": 60.0},
    "pullid":    {"max_calls": 3,  "window": 60.0},
    "pullmsg":   {"max_calls": 5,  "window": 60.0},
    "savequote": {"max_calls": 5,  "window": 60.0},
    "quote":     {"max_calls": 10, "window": 60.0},
    "lockdown":  {"max_calls": 5,  "window": 60.0},
    "poll":      {"max_calls": 3,  "window": 60.0},
}

# ── Lockdown abuse tracker ────────────────────────────────────
# tracks !lockdown server calls per guild — alerts owner if >1 in 5 minutes

_lockdown_calls: dict[int, list[tuple[float, int]]] = defaultdict(list)


def record_lockdown(guild_id: int, user_id: int) -> bool:
    """
    Record a !lockdown server call.
    Returns True if this looks like abuse (>1 call in 5 minutes from different users).
    """
    now = time.monotonic()
    window = 300.0  # 5 minutes
    _lockdown_calls[guild_id] = [
        (t, uid) for t, uid in _lockdown_calls[guild_id] if now - t < window
    ]
    _lockdown_calls[guild_id].append((now, user_id))
    unique_users = {uid for _, uid in _lockdown_calls[guild_id]}
    return len(unique_users) > 1


# ── Input validators ──────────────────────────────────────────

def validate_guild_channel(channel: discord.TextChannel, guild: discord.Guild) -> bool:
    return channel.guild.id == guild.id

def validate_guild_member(member: discord.Member, guild: discord.Guild) -> bool:
    return member.guild.id == guild.id

def validate_message_id(message_id: int) -> bool:
    return 10**16 <= message_id <= 10**19

def validate_user_id(user_id: int) -> bool:
    return 10**16 <= user_id <= 10**19

# ── Permission check ──────────────────────────────────────────

def can_use_command(member: discord.Member, config: dict) -> bool:
    if member.guild_permissions.administrator:
        return True
    role_id = config.get("quotesave_role")
    if not role_id:
        return True
    return any(r.id == role_id for r in member.roles)


# ── Helper: DM the bot owner ──────────────────────────────────

async def alert_owner(bot: commands.Bot, message: str) -> None:
    """Send a silent DM alert to the bot owner."""
    try:
        app = await bot.application_info()
        owner = app.owner
        if owner:
            await owner.send(f"🔔 **Lamarque Bot Alert**\n{message}")
    except Exception as e:
        print(f"[SECURITY] Failed to DM owner: {e}")


# ── Security cog ──────────────────────────────────────────────

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_check(self.global_security_check)

    def cog_unload(self):
        self.bot.remove_check(self.global_security_check)

    async def global_security_check(self, ctx: commands.Context) -> bool:
        """
        Runs before every prefix command.
        Checks: DM blocking → allowlist → rate limit.
        """
        # ── 0. Allow test runner bot ─────────────────────────
        TEST_BOT_ID = 1520264910523727953
        if ctx.author.id == TEST_BOT_ID:
            return True

        # ── 1. Block DM commands ──────────────────────────────
        if ctx.guild is None:
            await ctx.send("❌ Commands only work in servers, not DMs.")
            return False

        # ── 2. Allowlist check ────────────────────────────────
        allowlisted = await is_allowlisted(ctx.guild.id)
        if not allowlisted:
            # auto-add on first use — removes need for manual allowlisting
            # remove this line if you want strict allowlist enforcement
            await add_to_allowlist(ctx.guild.id)

        # ── 3. Rate limit check ───────────────────────────────
        command_name = ctx.command.name if ctx.command else None
        if command_name in LIMITS:
            cfg = LIMITS[command_name]
            allowed = rate_limiter.is_allowed(
                ctx.author.id, command_name, cfg["max_calls"], cfg["window"]
            )
            if not allowed:
                remaining = rate_limiter.time_remaining(
                    ctx.author.id, command_name, cfg["window"]
                )
                await ctx.send(
                    f"⏳ Slow down. You can use `!{command_name}` again in **{remaining:.1f}s**.",
                    delete_after=5
                )
                # alert owner if someone is hammering commands
                if remaining > cfg["window"] * 0.8:
                    await alert_owner(
                        self.bot,
                        f"⚠️ Rate limit abuse detected\n"
                        f"User: {ctx.author} (`{ctx.author.id}`)\n"
                        f"Command: `!{command_name}`\n"
                        f"Server: {ctx.guild.name} (`{ctx.guild.id}`)"
                    )
                return False

        # ── 4. Log the action ─────────────────────────────────
        if command_name:
            await log_action(
                ctx.guild.id,
                ctx.author.id,
                str(ctx.author),
                command_name,
                ctx.message.content[:100]
            )

        return True

    # ── Error handler ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.", delete_after=5)
            await alert_owner(
                self.bot,
                f"⚠️ Permission bypass attempt\n"
                f"User: {ctx.author} (`{ctx.author.id}`)\n"
                f"Command: `!{ctx.command}`\n"
                f"Server: {ctx.guild.name if ctx.guild else 'DM'}"
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}", delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            pass
        else:
            print(f"[ERROR] {ctx.command}: {error}")
            await ctx.send("❌ Something went wrong. Try again.", delete_after=5)

    # ── Allowlist management ──────────────────────────────────

    @commands.command()
    @commands.is_owner()
    async def allowserver(self, ctx, guild_id: int = None):
        """Add a server to the allowlist. Owner only."""
        target_id = guild_id or ctx.guild.id
        await add_to_allowlist(target_id)
        await ctx.send(f"✅ Server `{target_id}` added to allowlist.", delete_after=10)

    @commands.command()
    @commands.is_owner()
    async def denyserver(self, ctx, guild_id: int):
        """Remove a server from the allowlist. Owner only."""
        await remove_from_allowlist(guild_id)
        await ctx.send(f"✅ Server `{guild_id}` removed from allowlist.", delete_after=10)

    @commands.command()
    @commands.is_owner()
    async def allowlist(self, ctx):
        """Show all allowlisted servers. Owner only."""
        servers = await get_allowlist()
        if not servers:
            await ctx.send("No servers on the allowlist.")
            return
        lines = [f"• `{gid}`" for gid in servers]
        await ctx.send("✅ **Allowlisted Servers:**\n" + "\n".join(lines))

    # ── Guild join/leave events ───────────────────────────────

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Alert owner when bot joins a new server."""
        await alert_owner(
            self.bot,
            f"📥 Bot joined a new server\n"
            f"Name: **{guild.name}**\n"
            f"ID: `{guild.id}`\n"
            f"Members: {guild.member_count}\n"
            f"Owner: {guild.owner}"
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Alert owner when bot is removed from a server."""
        await alert_owner(
            self.bot,
            f"📤 Bot removed from server\n"
            f"Name: **{guild.name}**\n"
            f"ID: `{guild.id}`"
        )


async def setup(bot):
    await bot.add_cog(Security(bot))
