import discord
from discord.ext import commands
from config_manager import config, set_config


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """Set welcome channel and optional custom message."""
        if channel.guild.id != ctx.guild.id:
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return
        await set_config("welcome_channel", channel.id)
        if message:
            await set_config("welcome_message", message)
        await ctx.send(
            f"✅ Welcome channel set to {channel.mention}\n"
            f"Message: `{message or 'Default — Welcome {user} to {server}!'}`"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx):
        """Preview the welcome message."""
        await self._send_welcome(ctx.author, ctx.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._send_welcome(member, member.guild)

    async def _send_welcome(self, member: discord.Member, guild: discord.Guild):
        channel_id = config.get("welcome_channel")
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        template = config.get("welcome_message", "👋 Welcome {user} to **{server}**!")
        message = template.replace("{user}", member.mention).replace("{server}", guild.name)

        embed = discord.Embed(description=message, color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{guild.member_count}")
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
