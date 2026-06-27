import io
import time
import discord
from discord.ext import commands
from config_manager import (
    config, set_config, save_config,
    get_audit_log, clear_saved_quotes, log_action
)

START_TIME = time.monotonic()


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── !ping ─────────────────────────────────────────────────

    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        uptime_seconds = int(time.monotonic() - START_TIME)
        h, remainder = divmod(uptime_seconds, 3600)
        m, s = divmod(remainder, 60)
        embed = discord.Embed(title="🏓 Pong", color=discord.Color.green())
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{h}h {m}m {s}s", inline=True)
        await ctx.send(embed=embed)

    # ── !status ───────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx):
        board_id = config.get("quoteboard_channel")
        feed_id = config.get("echo_feed_channel")
        interval = config.get("quote_interval", 30)
        pinned = config.get("pinned_users", {})
        saved = config.get("saved_quotes", [])
        role_id = config.get("quotesave_role")
        welcome_ch = config.get("welcome_channel")
        log_ch = config.get("log_channel")

        embed = discord.Embed(title="📊 Lamarque Bot Status", color=discord.Color.blurple())
        embed.add_field(name="Quoteboard", value=f"<#{board_id}>" if board_id else "❌ Not set", inline=True)
        embed.add_field(name="Echo Feed", value=f"<#{feed_id}>" if feed_id else "❌ Not set", inline=True)
        embed.add_field(name="Feed Interval", value=f"{interval} minutes", inline=True)
        embed.add_field(name="Quotes Saved", value=str(len(saved)), inline=True)
        embed.add_field(name="Pinned Users", value=str(len(pinned)), inline=True)
        embed.add_field(name="Quote Role", value=f"<@&{role_id}>" if role_id else "Everyone", inline=True)
        embed.add_field(name="Welcome Channel", value=f"<#{welcome_ch}>" if welcome_ch else "❌ Not set", inline=True)
        embed.add_field(name="Log Channel", value=f"<#{log_ch}>" if log_ch else "❌ Not set", inline=True)
        embed.set_footer(text=f"Latency: {round(self.bot.latency * 1000)}ms")
        await ctx.send(embed=embed)

    # ── !setup ────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """Guided setup flow for all bot config."""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("🔧 **Lamarque Bot Setup**\nType `skip` to skip any step.\n\n**Step 1/5:** Mention the quoteboard channel:")
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() != "skip" and msg.channel_mentions:
                await set_config("quoteboard_channel", msg.channel_mentions[0].id)
                await ctx.send(f"✅ Quoteboard set to {msg.channel_mentions[0].mention}")
        except Exception:
            await ctx.send("⏰ Timed out. Re-run `!setup` to try again.")
            return

        await ctx.send("**Step 2/5:** Mention the echo feed channel:")
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() != "skip" and msg.channel_mentions:
                await set_config("echo_feed_channel", msg.channel_mentions[0].id)
                await ctx.send(f"✅ Echo feed set to {msg.channel_mentions[0].mention}")
        except Exception:
            await ctx.send("⏰ Timed out.")
            return

        await ctx.send("**Step 3/5:** How many minutes between auto quotes? (number only):")
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() != "skip":
                try:
                    minutes = int(msg.content.strip())
                    if minutes >= 1:
                        await set_config("quote_interval", minutes)
                        feed_cog = self.bot.cogs.get("Feed")
                        if feed_cog:
                            feed_cog.quote_feed.change_interval(minutes=minutes)
                        await ctx.send(f"✅ Auto quote interval set to {minutes} minutes.")
                except ValueError:
                    await ctx.send("⚠️ Invalid number, skipped.")
        except Exception:
            await ctx.send("⏰ Timed out.")
            return

        await ctx.send("**Step 4/5:** Mention the welcome channel (or skip):")
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() != "skip" and msg.channel_mentions:
                await set_config("welcome_channel", msg.channel_mentions[0].id)
                await ctx.send(f"✅ Welcome channel set to {msg.channel_mentions[0].mention}")
        except Exception:
            await ctx.send("⏰ Timed out.")
            return

        await ctx.send("**Step 5/5:** Mention the log channel (or skip):")
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() != "skip" and msg.channel_mentions:
                await set_config("log_channel", msg.channel_mentions[0].id)
                await ctx.send(f"✅ Log channel set to {msg.channel_mentions[0].mention}")
        except Exception:
            await ctx.send("⏰ Timed out.")
            return

        await ctx.send("✅ **Setup complete!** Run `!status` to review your config.")
        await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "setup", "guided setup completed")

    # ── !resetquotes ──────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetquotes(self, ctx):
        saved = config.get("saved_quotes", [])
        count = len(saved)

        embed = discord.Embed(
            title="⚠️ Reset Saved Quotes",
            description=f"This will clear **{count}** saved quote IDs from the dedup list.\n"
                        f"Quotes in the quoteboard channel are **not deleted** — only the tracking list is cleared.\n\n"
                        f"Type `confirm` to proceed or `cancel` to abort.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "confirm":
                await clear_saved_quotes()
                await ctx.send(f"✅ Cleared {count} saved quote IDs.")
                await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "resetquotes", f"cleared {count} entries")
            else:
                await ctx.send("❌ Reset cancelled.")
        except Exception:
            await ctx.send("⏰ Timed out. Reset cancelled.")

    # ── !exportquotes ─────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def exportquotes(self, ctx):
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        await ctx.send("⏳ Fetching quotes... this may take a moment.")

        lines = []
        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                author = embed.author.name if embed.author else "Unknown"
                content = embed.description or ""
                footer = embed.footer.text if embed.footer else ""
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                lines.append(f"[{timestamp}] {author}: {content}")
                if footer:
                    lines.append(f"  ({footer})")
                lines.append("")

        if not lines:
            await ctx.send("❌ No quotes found in the quoteboard channel.")
            return

        output = "\n".join(lines)
        file = discord.File(
            io.BytesIO(output.encode("utf-8")),
            filename="quotes_export.txt"
        )
        try:
            await ctx.author.send("📋 Here are your exported quotes:", file=file)
            await ctx.send("✅ Quotes exported — check your DMs.")
        except discord.Forbidden:
            await ctx.send("❌ Couldn't DM you. Check your privacy settings.")

        await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "exportquotes", f"{len(lines)} lines exported")

    # ── !quoteboardstats ──────────────────────────────────────

    @commands.command()
    async def quoteboardstats(self, ctx):
        board_id = config.get("quoteboard_channel")
        if not board_id:
            await ctx.send("❌ No quoteboard channel set.", delete_after=5)
            return

        channel = self.bot.get_channel(board_id)
        if not channel:
            await ctx.send("❌ Quoteboard channel not found.", delete_after=5)
            return

        await ctx.send("⏳ Counting quotes...")

        counts: dict[str, int] = {}
        last_quote = None
        total = 0

        async for msg in channel.history(limit=500):
            if msg.author.bot and msg.embeds:
                embed = msg.embeds[0]
                author = embed.author.name if embed.author else "Unknown"
                counts[author] = counts.get(author, 0) + 1
                total += 1
                if last_quote is None:
                    last_quote = msg

        if total == 0:
            await ctx.send("❌ No quotes found.")
            return

        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = "\n".join(f"**{i+1}.** {name} — {count} quote{'s' if count != 1 else ''}" for i, (name, count) in enumerate(top))

        embed = discord.Embed(title="📊 Quoteboard Stats", color=discord.Color.gold())
        embed.add_field(name="Total Quotes", value=str(total), inline=True)
        embed.add_field(name="Unique Users", value=str(len(counts)), inline=True)
        if last_quote:
            embed.add_field(name="Last Quote", value=f"<t:{int(last_quote.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Top Quoted", value=top_str or "None", inline=False)
        await ctx.send(embed=embed)

    # ── !auditlog ─────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def auditlog(self, ctx, limit: int = 20):
        limit = min(limit, 50)
        entries = await get_audit_log(ctx.guild.id, limit)
        if not entries:
            await ctx.send("No audit log entries yet.")
            return

        lines = []
        for e in entries:
            lines.append(f"`{e['timestamp']}` **{e['user_name']}** — `!{e['command']}` {e['detail'][:50]}")

        output = "\n".join(lines)
        if len(output) > 1900:
            output = output[:1900] + "\n..."

        embed = discord.Embed(
            title=f"📋 Audit Log (last {len(entries)})",
            description=output,
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    # ── !help ─────────────────────────────────────────────────

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(title="Lamarque Bot — Commands", color=discord.Color.blurple())

        embed.add_field(name="📌 Quoteboard", value=
            "`!savequote` `!quote` `!pull @user` `!pullid <id>` `!pullmsg <id>`\n"
            "`!randomquote @user` `!quotecount @user` `!quoteleaderboard`\n"
            "`!deletequote <id>` `!quoteoftheday`",
            inline=False
        )
        embed.add_field(name="⚙️ Setup", value=
            "`!setup` `!status` `!setquoteboard` `!setechofeed`\n"
            "`!setquoterole` `!setquotestream` `!setwelcome` `!setlogchannel`\n"
            "`!quotestop` `!quotestart`",
            inline=False
        )
        embed.add_field(name="📊 Stats", value=
            "`!quoteboardstats` `!ping` `!auditlog`",
            inline=False
        )
        embed.add_field(name="👤 Pinned Users", value=
            "`!pinuser @user` `!unpinuser @user` `!pinnedusers`",
            inline=False
        )
        embed.add_field(name="🔒 Lockdown", value=
            "`!lockdown channel/user/role/server` `!unlock channel/user/role/server`",
            inline=False
        )
        embed.add_field(name="🛠️ Admin", value=
            "`!resetquotes` `!exportquotes` `!auditlog`",
            inline=False
        )
        embed.add_field(name="🎉 Fun", value=
            "`!poll \"question\" \"opt1\" \"opt2\"`",
            inline=False
        )
        embed.set_footer(text="Slash command versions available for most commands via /")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
