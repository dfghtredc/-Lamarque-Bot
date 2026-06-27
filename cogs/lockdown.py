import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
from cogs.security import alert_owner, record_lockdown
from config_manager import log_action

LOCKDOWN_GIF = "https://media.tenor.com/x8v1oNUOmg4AAAAC/lockdown.gif"


# ── Native confirmation view ──────────────────────────────────

class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=15)
        self.author = author
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ Only the command invoker can confirm this.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="🔒")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.send_message("❌ Action cancelled.", ephemeral=True)

    async def on_timeout(self):
        self.confirmed = False


# ── Lockdown cog ──────────────────────────────────────────────

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _lock_channel(self, channel: discord.TextChannel, guild: discord.Guild, lock: bool):
        await channel.set_permissions(guild.default_role, send_messages=not lock)

    async def _confirm(self, ctx, action: str) -> bool:
        """Native button confirmation."""
        view = ConfirmView(ctx.author)
        embed = discord.Embed(
            title=f"⚠️ Confirm {action}",
            description="This will affect the entire server. Are you sure?",
            color=discord.Color.orange()
        )
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()
        await msg.delete()
        return view.confirmed

    def _parse_duration(self, duration: str) -> int | None:
        try:
            if duration.endswith("m"):
                return int(duration[:-1]) * 60
            elif duration.endswith("h"):
                return int(duration[:-1]) * 3600
            elif duration.endswith("s"):
                return int(duration[:-1])
        except ValueError:
            return None
        return None

    # ── !lockdown ─────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, target: str, *, args: str = ""):
        guild = ctx.guild
        invoker = ctx.author.display_name

        # parse duration from end of args if present
        parts = args.strip().split()
        duration_str = None
        unlock_seconds = None

        if parts and (parts[-1].endswith("m") or parts[-1].endswith("h") or parts[-1].endswith("s")):
            duration_str = parts[-1]
            unlock_seconds = self._parse_duration(duration_str)
            if unlock_seconds is None:
                await ctx.send("❌ Invalid duration. Use `10m`, `1h`, or `30s`.", delete_after=5)
                return

        if target == "channel":
            channel = ctx.channel
            await self._lock_channel(channel, guild, lock=True)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(
                f"🔒 **#{channel.name}** locked by **{invoker}**"
                + (f" for **{duration_str}**" if duration_str else "")
            )
            await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", f"channel #{channel.name}")
            if unlock_seconds:
                await asyncio.sleep(unlock_seconds)
                await self._lock_channel(channel, guild, lock=False)
                await ctx.send(f"🔓 **#{channel.name}** auto-unlocked.")

        elif target == "user":
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            if not member:
                await ctx.send("❌ Please mention a user.", delete_after=5)
                return
            timeout_duration = timedelta(seconds=unlock_seconds) if unlock_seconds else timedelta(hours=1)
            try:
                await member.timeout(timeout_duration, reason=f"Locked by {invoker}")
                await ctx.send(LOCKDOWN_GIF)
                await ctx.send(
                    f"🔒 **{member.display_name}** timed out by **{invoker}**"
                    + (f" for **{duration_str}**" if duration_str else " for **1h**")
                )
                await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", f"user {member}")
            except discord.Forbidden:
                await ctx.send("❌ Missing permission to timeout this user.", delete_after=5)

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.", delete_after=5)
                return
            timeout_duration = timedelta(seconds=unlock_seconds) if unlock_seconds else timedelta(hours=1)
            failed = 0
            for member in role.members:
                try:
                    await member.timeout(timeout_duration, reason=f"Role locked by {invoker}")
                except discord.Forbidden:
                    failed += 1
            await ctx.send(LOCKDOWN_GIF)
            msg = f"🔒 **{role.name}** role timed out by **{invoker}**"
            if failed:
                msg += f" ({failed} members skipped — missing permissions)"
            await ctx.send(msg)
            await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", f"role {role.name}")

        elif target == "server":
            confirmed = await self._confirm(ctx, "Server Lockdown")
            if not confirmed:
                await ctx.send("❌ Lockdown cancelled.", delete_after=5)
                return

            is_abuse = record_lockdown(guild.id, ctx.author.id)
            if is_abuse:
                await alert_owner(
                    self.bot,
                    f"⚠️ Lockdown abuse detected\n"
                    f"Server: {guild.name} (`{guild.id}`)\n"
                    f"Triggered by: {ctx.author} (`{ctx.author.id}`)"
                )

            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=True)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{guild.name}** locked by **{invoker}**")
            await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", "server")

        else:
            await ctx.send(
                "❌ Usage: `!lockdown channel/user @user/role @role/server [duration]`\n"
                "Duration: `10m`, `1h`, `30s`",
                delete_after=5
            )

    # ── !unlock ───────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, target: str):
        guild = ctx.guild
        invoker = ctx.author.display_name

        if target == "channel":
            await self._lock_channel(ctx.channel, guild, lock=False)
            await ctx.send(f"🔓 **#{ctx.channel.name}** unlocked by **{invoker}**")

        elif target == "user":
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            if not member:
                await ctx.send("❌ Please mention a user.", delete_after=5)
                return
            try:
                await member.timeout(None, reason=f"Unlocked by {invoker}")
                await ctx.send(f"🔓 **{member.display_name}** timeout removed by **{invoker}**")
            except discord.Forbidden:
                await ctx.send("❌ Missing permission to remove timeout.", delete_after=5)

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.", delete_after=5)
                return
            for member in role.members:
                try:
                    await member.timeout(None, reason=f"Role unlocked by {invoker}")
                except discord.Forbidden:
                    pass
            await ctx.send(f"🔓 **{role.name}** role timeout removed by **{invoker}**")

        elif target == "server":
            confirmed = await self._confirm(ctx, "Server Unlock")
            if not confirmed:
                await ctx.send("❌ Unlock cancelled.", delete_after=5)
                return
            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=False)
            await ctx.send(f"🔓 **{guild.name}** unlocked by **{invoker}**")
            await log_action(guild.id, ctx.author.id, str(ctx.author), "unlock", "server")

        else:
            await ctx.send("❌ Usage: `!unlock channel/user @user/role @role/server`", delete_after=5)

    # ── slash commands — fully implemented ────────────────────

    @app_commands.command(name="lockdown", description="Lock down a channel, user, role, or server")
    @app_commands.describe(
        target="channel / user / role / server",
        user="User to lock (for user target)",
        role="Role to lock (for role target)",
        duration="Duration e.g. 10m, 1h, 30s"
    )
    @app_commands.choices(target=[
        app_commands.Choice(name="channel", value="channel"),
        app_commands.Choice(name="user", value="user"),
        app_commands.Choice(name="role", value="role"),
        app_commands.Choice(name="server", value="server"),
    ])
    async def slash_lockdown(
        self,
        interaction: discord.Interaction,
        target: str,
        user: discord.Member = None,
        role: discord.Role = None,
        duration: str = None
    ):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return

        guild = interaction.guild
        invoker = interaction.user.display_name
        unlock_seconds = self._parse_duration(duration) if duration else None

        await interaction.response.defer()

        if target == "channel":
            channel = interaction.channel
            await self._lock_channel(channel, guild, lock=True)
            await interaction.followup.send(LOCKDOWN_GIF)
            await interaction.followup.send(
                f"🔒 **#{channel.name}** locked by **{invoker}**"
                + (f" for **{duration}**" if duration else "")
            )
            await log_action(guild.id, interaction.user.id, str(interaction.user), "lockdown", f"channel #{channel.name}")
            if unlock_seconds:
                await asyncio.sleep(unlock_seconds)
                await self._lock_channel(channel, guild, lock=False)
                await interaction.followup.send(f"🔓 **#{channel.name}** auto-unlocked.")

        elif target == "user":
            if not user:
                await interaction.followup.send("❌ Please specify a user.", ephemeral=True)
                return
            timeout_duration = timedelta(seconds=unlock_seconds) if unlock_seconds else timedelta(hours=1)
            try:
                await user.timeout(timeout_duration, reason=f"Locked by {invoker}")
                await interaction.followup.send(LOCKDOWN_GIF)
                await interaction.followup.send(
                    f"🔒 **{user.display_name}** timed out by **{invoker}**"
                    + (f" for **{duration}**" if duration else " for **1h**")
                )
                await log_action(guild.id, interaction.user.id, str(interaction.user), "lockdown", f"user {user}")
            except discord.Forbidden:
                await interaction.followup.send("❌ Missing permission to timeout this user.", ephemeral=True)

        elif target == "role":
            if not role:
                await interaction.followup.send("❌ Please specify a role.", ephemeral=True)
                return
            timeout_duration = timedelta(seconds=unlock_seconds) if unlock_seconds else timedelta(hours=1)
            for member in role.members:
                try:
                    await member.timeout(timeout_duration, reason=f"Role locked by {invoker}")
                except discord.Forbidden:
                    pass
            await interaction.followup.send(LOCKDOWN_GIF)
            await interaction.followup.send(f"🔒 **{role.name}** role timed out by **{invoker}**")
            await log_action(guild.id, interaction.user.id, str(interaction.user), "lockdown", f"role {role.name}")

        elif target == "server":
            view = ConfirmView(interaction.user)
            embed = discord.Embed(
                title="⚠️ Confirm Server Lockdown",
                description="This will lock every text channel. Are you sure?",
                color=discord.Color.orange()
            )
            confirm_msg = await interaction.followup.send(embed=embed, view=view)
            await view.wait()
            await confirm_msg.delete()

            if not view.confirmed:
                await interaction.followup.send("❌ Lockdown cancelled.", ephemeral=True)
                return

            is_abuse = record_lockdown(guild.id, interaction.user.id)
            if is_abuse:
                await alert_owner(
                    self.bot,
                    f"⚠️ Lockdown abuse detected\n"
                    f"Server: {guild.name} (`{guild.id}`)\n"
                    f"Triggered by: {interaction.user} (`{interaction.user.id}`)"
                )

            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=True)
            await interaction.followup.send(LOCKDOWN_GIF)
            await interaction.followup.send(f"🔒 **{guild.name}** locked by **{invoker}**")
            await log_action(guild.id, interaction.user.id, str(interaction.user), "lockdown", "server")

    @app_commands.command(name="unlock", description="Unlock a channel, user, role, or server")
    @app_commands.describe(
        target="channel / user / role / server",
        user="User to unlock (for user target)",
        role="Role to unlock (for role target)"
    )
    @app_commands.choices(target=[
        app_commands.Choice(name="channel", value="channel"),
        app_commands.Choice(name="user", value="user"),
        app_commands.Choice(name="role", value="role"),
        app_commands.Choice(name="server", value="server"),
    ])
    async def slash_unlock(
        self,
        interaction: discord.Interaction,
        target: str,
        user: discord.Member = None,
        role: discord.Role = None
    ):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return

        guild = interaction.guild
        invoker = interaction.user.display_name
        await interaction.response.defer()

        if target == "channel":
            await self._lock_channel(interaction.channel, guild, lock=False)
            await interaction.followup.send(f"🔓 **#{interaction.channel.name}** unlocked by **{invoker}**")

        elif target == "user":
            if not user:
                await interaction.followup.send("❌ Please specify a user.", ephemeral=True)
                return
            try:
                await user.timeout(None, reason=f"Unlocked by {invoker}")
                await interaction.followup.send(f"🔓 **{user.display_name}** timeout removed by **{invoker}**")
            except discord.Forbidden:
                await interaction.followup.send("❌ Missing permission.", ephemeral=True)

        elif target == "role":
            if not role:
                await interaction.followup.send("❌ Please specify a role.", ephemeral=True)
                return
            for member in role.members:
                try:
                    await member.timeout(None, reason=f"Role unlocked by {invoker}")
                except discord.Forbidden:
                    pass
            await interaction.followup.send(f"🔓 **{role.name}** role timeout removed by **{invoker}**")

        elif target == "server":
            view = ConfirmView(interaction.user)
            embed = discord.Embed(
                title="⚠️ Confirm Server Unlock",
                description="This will unlock every text channel. Are you sure?",
                color=discord.Color.orange()
            )
            confirm_msg = await interaction.followup.send(embed=embed, view=view)
            await view.wait()
            await confirm_msg.delete()

            if not view.confirmed:
                await interaction.followup.send("❌ Unlock cancelled.", ephemeral=True)
                return

            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=False)
            await interaction.followup.send(f"🔓 **{guild.name}** unlocked by **{invoker}**")
            await log_action(guild.id, interaction.user.id, str(interaction.user), "unlock", "server")


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
