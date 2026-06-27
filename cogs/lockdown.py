import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from cogs.security import alert_owner, record_lockdown
from config_manager import log_action

LOCKDOWN_GIF = "https://media.tenor.com/x8v1oNUOmg4AAAAC/lockdown.gif"


class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_muted_role(self, guild: discord.Guild) -> discord.Role | None:
        return discord.utils.get(guild.roles, name="Muted")

    async def _lock_channel(self, channel: discord.TextChannel, guild: discord.Guild, lock: bool):
        await channel.set_permissions(guild.default_role, send_messages=not lock)

    async def _confirm(self, ctx, action: str) -> bool:
        """Ask for confirmation. Returns True if confirmed."""
        embed = discord.Embed(
            title=f"⚠️ Confirm {action}",
            description=f"Type `confirm` to proceed or `cancel` to abort.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=15)
            return msg.content.lower() == "confirm"
        except asyncio.TimeoutError:
            await ctx.send("⏰ Timed out. Action cancelled.", delete_after=5)
            return False

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, target: str, entity=None, duration: str = None):
        guild = ctx.guild
        invoker = ctx.author.display_name

        # parse optional duration — e.g. "10m", "1h"
        unlock_seconds = None
        if duration:
            try:
                if duration.endswith("m"):
                    unlock_seconds = int(duration[:-1]) * 60
                elif duration.endswith("h"):
                    unlock_seconds = int(duration[:-1]) * 3600
                elif duration.endswith("s"):
                    unlock_seconds = int(duration[:-1])
            except ValueError:
                await ctx.send("❌ Invalid duration. Use `10m`, `1h`, or `30s`.", delete_after=5)
                return

        if target == "channel":
            channel = ctx.channel
            await self._lock_channel(channel, guild, lock=True)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **#{channel.name}** locked by **{invoker}**" +
                          (f" for **{duration}**" if duration else ""))
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
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            await member.add_roles(muted_role)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{member.display_name}** locked by **{invoker}**" +
                          (f" for **{duration}**" if duration else ""))
            await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", f"user {member}")
            if unlock_seconds:
                await asyncio.sleep(unlock_seconds)
                await member.remove_roles(muted_role)
                await ctx.send(f"🔓 **{member.display_name}** auto-unmuted.")

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.", delete_after=5)
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            for member in role.members:
                await member.add_roles(muted_role)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{role.name}** locked by **{invoker}**")
            await log_action(guild.id, ctx.author.id, str(ctx.author), "lockdown", f"role {role.name}")

        elif target == "server":
            # confirmation required for server lockdown
            confirmed = await self._confirm(ctx, "Server Lockdown")
            if not confirmed:
                await ctx.send("❌ Lockdown cancelled.")
                return

            # abuse detection
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
            await ctx.send("❌ Usage: `!lockdown channel/user/role/server [duration]`", delete_after=5)

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
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{member.display_name}** unlocked by **{invoker}**")

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.", delete_after=5)
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            for member in role.members:
                await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{role.name}** unlocked by **{invoker}**")

        elif target == "server":
            confirmed = await self._confirm(ctx, "Server Unlock")
            if not confirmed:
                await ctx.send("❌ Unlock cancelled.")
                return
            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=False)
            await ctx.send(f"🔓 **{guild.name}** unlocked by **{invoker}**")
            await log_action(guild.id, ctx.author.id, str(ctx.author), "unlock", "server")

        else:
            await ctx.send("❌ Usage: `!unlock channel/user/role/server`", delete_after=5)

    @app_commands.command(name="lockdown", description="Lock down a channel, user, role, or server")
    @app_commands.describe(target="channel / user / role / server", duration="Optional duration e.g. 10m, 1h")
    async def slash_lockdown(self, interaction: discord.Interaction, target: str, duration: str = None):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return
        await interaction.response.send_message(f"Use `!lockdown {target}` for now.")

    @app_commands.command(name="unlock", description="Unlock a channel, user, role, or server")
    @app_commands.describe(target="channel / user / role / server")
    async def slash_unlock(self, interaction: discord.Interaction, target: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return
        await interaction.response.send_message(f"Use `!unlock {target}` for now.")


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
