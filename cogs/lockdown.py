import discord
from discord import app_commands
from discord.ext import commands

LOCKDOWN_GIF = "https://media.tenor.com/x8v1oNUOmg4AAAAC/lockdown.gif"


class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_muted_role(self, guild: discord.Guild) -> discord.Role | None:
        return discord.utils.get(guild.roles, name="Muted")

    async def _lock_channel(self, channel: discord.TextChannel, guild: discord.Guild, lock: bool):
        await channel.set_permissions(guild.default_role, send_messages=not lock)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, target: str, entity: discord.TextChannel | discord.Member | discord.Role = None):
        guild = ctx.guild
        invoker = ctx.author.display_name

        if target == "channel":
            channel = entity if isinstance(entity, discord.TextChannel) else ctx.channel
            if channel.guild.id != guild.id:
                await ctx.send("❌ That channel isn't in this server.", delete_after=5)
                return
            await self._lock_channel(channel, guild, lock=True)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **#{channel.name}** has been locked down by **{invoker}**")

        elif target == "user":
            member = entity if isinstance(entity, discord.Member) else (ctx.message.mentions[0] if ctx.message.mentions else None)
            if not member:
                await ctx.send("❌ Please mention a user.", delete_after=5)
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            await member.add_roles(muted_role)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{member.display_name}** has been locked down by **{invoker}**")

        elif target == "role":
            role = entity if isinstance(entity, discord.Role) else (ctx.message.role_mentions[0] if ctx.message.role_mentions else None)
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
            await ctx.send(f"🔒 **{role.name}** role has been locked down by **{invoker}**")

        elif target == "server":
            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=True)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{guild.name}** has been locked down by **{invoker}**")

        else:
            await ctx.send("❌ Usage: `!lockdown channel/user @user/role @role/server`", delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, target: str, entity: discord.TextChannel | discord.Member | discord.Role = None):
        guild = ctx.guild
        invoker = ctx.author.display_name

        if target == "channel":
            channel = entity if isinstance(entity, discord.TextChannel) else ctx.channel
            await self._lock_channel(channel, guild, lock=False)
            await ctx.send(f"🔓 **#{channel.name}** has been unlocked by **{invoker}**")

        elif target == "user":
            member = entity if isinstance(entity, discord.Member) else (ctx.message.mentions[0] if ctx.message.mentions else None)
            if not member:
                await ctx.send("❌ Please mention a user.", delete_after=5)
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{member.display_name}** has been unlocked by **{invoker}**")

        elif target == "role":
            role = entity if isinstance(entity, discord.Role) else (ctx.message.role_mentions[0] if ctx.message.role_mentions else None)
            if not role:
                await ctx.send("❌ Please mention a role.", delete_after=5)
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.", delete_after=5)
                return
            for member in role.members:
                await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{role.name}** role has been unlocked by **{invoker}**")

        elif target == "server":
            for channel in guild.text_channels:
                await self._lock_channel(channel, guild, lock=False)
            await ctx.send(f"🔓 **{guild.name}** has been unlocked by **{invoker}**")

        else:
            await ctx.send("❌ Usage: `!unlock channel/user @user/role @role/server`", delete_after=5)

    @app_commands.command(name="lockdown", description="Lock down a channel, user, role, or server")
    @app_commands.describe(target="channel / user / role / server")
    async def slash_lockdown(self, interaction: discord.Interaction, target: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return
        await interaction.response.send_message(f"Use `!lockdown {target}` — full slash support coming next.")

    @app_commands.command(name="unlock", description="Unlock a channel, user, role, or server")
    @app_commands.describe(target="channel / user / role / server")
    async def slash_unlock(self, interaction: discord.Interaction, target: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
            return
        await interaction.response.send_message(f"Use `!unlock {target}` — full slash support coming next.")


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
