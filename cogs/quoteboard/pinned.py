import discord
from discord import app_commands
from discord.ext import commands
from config_manager import config, save_config
from cogs.security import validate_guild_channel
from .helpers import save_to_quoteboard


class Pinned(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pinuser(self, ctx, user: discord.Member, channel: discord.TextChannel = None):
        if channel and not validate_guild_channel(channel, ctx.guild):
            await ctx.send("❌ That channel isn't in this server.", delete_after=5)
            return

        pinned = config.get("pinned_users", {})
        pinned[str(user.id)] = channel.id if channel else None
        config["pinned_users"] = pinned
        save_config()
        location = f"in {channel.mention}" if channel else "everywhere"
        await ctx.send(f"✅ Now tracking **{user.display_name}** {location}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unpinuser(self, ctx, user: discord.Member, channel: discord.TextChannel = None):
        pinned = config.get("pinned_users", {})
        uid = str(user.id)
        if uid not in pinned:
            await ctx.send(f"❌ {user.display_name} is not pinned.", delete_after=5)
            return
        if channel:
            if pinned[uid] == channel.id:
                del pinned[uid]
                config["pinned_users"] = pinned
                save_config()
                await ctx.send(f"✅ Stopped tracking **{user.display_name}** in {channel.mention}.")
            else:
                await ctx.send(f"❌ {user.display_name} is not pinned in {channel.mention}.", delete_after=5)
        else:
            del pinned[uid]
            config["pinned_users"] = pinned
            save_config()
            await ctx.send(f"✅ Stopped tracking **{user.display_name}**.")

    @commands.command()
    async def pinnedusers(self, ctx):
        pinned = config.get("pinned_users", {})
        if not pinned:
            await ctx.send("No pinned users.")
            return
        lines = []
        for uid, cid in pinned.items():
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown ({uid})"
            location = f"<#{cid}>" if cid else "everywhere"
            lines.append(f"• **{name}** — {location}")
        await ctx.send("📌 **Pinned Users:**\n" + "\n".join(lines))

    @commands.Cog.listener()
    async def on_message(self, message):
        # ── early exits — no I/O until all checks pass ────────
        if message.author.bot:
            return
        if message.guild is None:
            return

        pinned = config.get("pinned_users", {})

        # fast path — nothing pinned
        if not pinned:
            return

        uid = str(message.author.id)
        if uid not in pinned:
            return

        watched_channel = pinned[uid]
        if watched_channel and message.channel.id != watched_channel:
            return

        # guild scope check
        if not validate_guild_channel(message.channel, message.guild):
            return

        result = await save_to_quoteboard(
            self.bot, message, message.channel, "auto-tracked"
        )

        if result:
            feed_id = config.get("echo_feed_channel")
            if feed_id:
                feed_channel = self.bot.get_channel(feed_id)
                if feed_channel and validate_guild_channel(feed_channel, message.guild):
                    await feed_channel.send(embed=result.embeds[0])

    @app_commands.command(name="pinuser", description="Pin a user for real-time quote tracking")
    @app_commands.describe(user="User to pin", channel="Optional channel to track them in")
    async def slash_pinuser(self, interaction: discord.Interaction, user: discord.Member, channel: discord.TextChannel = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admins only.", ephemeral=True)
            return
        if channel and not validate_guild_channel(channel, interaction.guild):
            await interaction.response.send_message("❌ That channel isn't in this server.", ephemeral=True)
            return
        pinned = config.get("pinned_users", {})
        pinned[str(user.id)] = channel.id if channel else None
        config["pinned_users"] = pinned
        save_config()
        location = f"in {channel.mention}" if channel else "everywhere"
        await interaction.response.send_message(f"✅ Now tracking **{user.display_name}** {location}.")

    @app_commands.command(name="pinnedusers", description="Show all pinned users")
    async def slash_pinnedusers(self, interaction: discord.Interaction):
        pinned = config.get("pinned_users", {})
        if not pinned:
            await interaction.response.send_message("No pinned users.", ephemeral=True)
            return
        lines = []
        for uid, cid in pinned.items():
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown ({uid})"
            location = f"<#{cid}>" if cid else "everywhere"
            lines.append(f"• **{name}** — {location}")
        await interaction.response.send_message("📌 **Pinned Users:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Pinned(bot))
