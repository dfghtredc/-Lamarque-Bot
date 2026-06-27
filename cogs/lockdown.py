import discord
from discord.ext import commands

LOCKDOWN_GIF = "https://media.tenor.com/x8v1oNUOmg4AAAAC/lockdown.gif"

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_muted_role(self, guild):
        return discord.utils.get(guild.roles, name="Muted")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, target: str, *, entity: str = None):
        guild = ctx.guild
        invoker = ctx.author.display_name

        if target == "channel":
            channel = ctx.channel if not entity else discord.utils.get(guild.text_channels, mention=entity)
            await channel.set_permissions(guild.default_role, send_messages=False)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **#{channel.name}** has been locked down by **{invoker}**")

        elif target == "user":
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            if not member:
                await ctx.send("❌ Please mention a user.")
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.")
                return
            await member.add_roles(muted_role)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{member.display_name}** has been locked down by **{invoker}**")

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.")
                return
            muted_role = self.get_muted_role(guild)
            if not muted_role:
                await ctx.send("❌ No Muted role found.")
                return
            for member in role.members:
                await member.add_roles(muted_role)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{role.name}** role has been locked down by **{invoker}**")

        elif target == "server":
            for channel in guild.text_channels:
                await channel.set_permissions(guild.default_role, send_messages=False)
            await ctx.send(LOCKDOWN_GIF)
            await ctx.send(f"🔒 **{guild.name}** has been locked down by **{invoker}**")

        else:
            await ctx.send("❌ Usage: `!lockdown channel/user/role/server`")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, target: str):
        guild = ctx.guild
        invoker = ctx.author.display_name

        if target == "channel":
            await ctx.channel.set_permissions(guild.default_role, send_messages=True)
            await ctx.send(f"🔓 **#{ctx.channel.name}** has been unlocked by **{invoker}**")

        elif target == "user":
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            if not member:
                await ctx.send("❌ Please mention a user.")
                return
            muted_role = self.get_muted_role(guild)
            await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{member.display_name}** has been unlocked by **{invoker}**")

        elif target == "role":
            role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
            if not role:
                await ctx.send("❌ Please mention a role.")
                return
            muted_role = self.get_muted_role(guild)
            for member in role.members:
                await member.remove_roles(muted_role)
            await ctx.send(f"🔓 **{role.name}** role has been unlocked by **{invoker}**")

        elif target == "server":
            for channel in guild.text_channels:
                await channel.set_permissions(guild.default_role, send_messages=True)
            await ctx.send(f"🔓 **{guild.name}** has been unlocked by **{invoker}**")

        else:
            await ctx.send("❌ Usage: `!unlock channel/user/role/server`")

async def setup(bot):
    await bot.add_cog(Lockdown(bot))