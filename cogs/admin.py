import io
import time
import discord
from discord import app_commands
from discord.ext import commands
from config_manager import (
    config, set_config, save_config,
    get_audit_log, clear_saved_quotes, log_action
)

START_TIME = time.monotonic()


# ── Setup Modal ───────────────────────────────────────────────

class SetupModal(discord.ui.Modal, title="Lamarque Bot Setup"):
    quoteboard = discord.ui.TextInput(
        label="Quoteboard Channel ID",
        placeholder="Right-click channel → Copy Channel ID",
        required=False
    )
    echo_feed = discord.ui.TextInput(
        label="Echo Feed Channel ID",
        placeholder="Right-click channel → Copy Channel ID",
        required=False
    )
    interval = discord.ui.TextInput(
        label="Auto Quote Interval (minutes)",
        placeholder="e.g. 30",
        required=False,
        max_length=4
    )
    welcome = discord.ui.TextInput(
        label="Welcome Channel ID",
        placeholder="Right-click channel → Copy Channel ID",
        required=False
    )
    log_channel = discord.ui.TextInput(
        label="Log Channel ID",
        placeholder="Right-click channel → Copy Channel ID",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        results = []

        if self.quoteboard.value:
            try:
                ch_id = int(self.quoteboard.value.strip())
                ch = interaction.guild.get_channel(ch_id)
                if ch:
                    await set_config("quoteboard_channel", ch_id)
                    results.append(f"✅ Quoteboard → {ch.mention}")
                else:
                    results.append("❌ Quoteboard channel not found")
            except ValueError:
                results.append("❌ Invalid quoteboard channel ID")

        if self.echo_feed.value:
            try:
                ch_id = int(self.echo_feed.value.strip())
                ch = interaction.guild.get_channel(ch_id)
                if ch:
                    await set_config("echo_feed_channel", ch_id)
                    results.append(f"✅ Echo feed → {ch.mention}")
                else:
                    results.append("❌ Echo feed channel not found")
            except ValueError:
                results.append("❌ Invalid echo feed channel ID")

        if self.interval.value:
            try:
                minutes = int(self.interval.value.strip())
                if minutes >= 1:
                    await set_config("quote_interval", minutes)
                    results.append(f"✅ Auto quote interval → {minutes} minutes")
                else:
                    results.append("❌ Interval must be at least 1 minute")
            except ValueError:
                results.append("❌ Invalid interval")

        if self.welcome.value:
            try:
                ch_id = int(self.welcome.value.strip())
                ch = interaction.guild.get_channel(ch_id)
                if ch:
                    await set_config("welcome_channel", ch_id)
                    results.append(f"✅ Welcome → {ch.mention}")
                else:
                    results.append("❌ Welcome channel not found")
            except ValueError:
                results.append("❌ Invalid welcome channel ID")

        if self.log_channel.value:
            try:
                ch_id = int(self.log_channel.value.strip())
                ch = interaction.guild.get_channel(ch_id)
                if ch:
                    await set_config("log_channel", ch_id)
                    results.append(f"✅ Log → {ch.mention}")
                else:
                    results.append("❌ Log channel not found")
            except ValueError:
                results.append("❌ Invalid log channel ID")

        if not results:
            await interaction.response.send_message("⚠️ No fields were filled in.", ephemeral=True)
            return

        await interaction.response.send_message(
            "**Setup Results:**\n" + "\n".join(results),
            ephemeral=True
        )
        await log_action(
            interaction.guild.id,
            interaction.user.id,
            str(interaction.user),
            "setup",
            "modal setup completed"
        )


# ── Reset confirmation view ───────────────────────────────────

class ResetConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=30)
        self.author = author
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Not your confirmation.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.send_message("❌ Reset cancelled.", ephemeral=True)


# ── Admin cog ─────────────────────────────────────────────────

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

    # ── !setup — opens native Modal ───────────────────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """Opens a native Discord modal for bot setup."""
        await ctx.send(
            "Click below to open the setup form:",
            view=SetupLaunchView()
        )

    # ── !resetquotes — native button confirmation ─────────────

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetquotes(self, ctx):
        saved = config.get("saved_quotes", [])
        count = len(saved)

        view = ResetConfirmView(ctx.author)
        embed = discord.Embed(
            title="⚠️ Reset Saved Quotes",
            description=(
                f"This will clear **{count}** saved quote IDs from the dedup list.\n"
                f"Quotes in the quoteboard channel are **not deleted** — only the tracking list is cleared."
            ),
            color=discord.Color.orange()
        )
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()
        await msg.delete()

        if view.confirmed:
            await clear_saved_quotes()
            await ctx.send(f"✅ Cleared {count} saved quote IDs.")
            await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "resetquotes", f"cleared {count} entries")
        else:
            await ctx.send("❌ Reset cancelled.", delete_after=5)

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

        await ctx.send("⏳ Fetching quotes...")

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
            await ctx.send("❌ No quotes found.")
            return

        output = "\n".join(lines)
        file = discord.File(io.BytesIO(output.encode("utf-8")), filename="quotes_export.txt")
        try:
            await ctx.author.send("📋 Here are your exported quotes:", file=file)
            await ctx.send("✅ Quotes exported — check your DMs.")
        except discord.Forbidden:
            await ctx.send("❌ Couldn't DM you. Check your privacy settings.")

        await log_action(ctx.guild.id, ctx.author.id, str(ctx.author), "exportquotes", f"{len(lines)} lines")

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
        top_str = "\n".join(
            f"**{i+1}.** {name} — {count} quote{'s' if count != 1 else ''}"
            for i, (name, count) in enumerate(top)
        )

        embed = discord.Embed(title="📊 Quoteboard Stats", color=discord.Color.gold())
        embed.add_field(name="Total Quotes", value=str(total), inline=True)
        embed.add_field(name="Unique Users", value=str(len(counts)), inline=True)
        if last_quote:
            embed.add_field(
                name="Last Quote",
                value=f"<t:{int(last_quote.created_at.timestamp())}:R>",
                inline=True
            )
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

        lines = [
            f"`{e['timestamp']}` **{e['user_name']}** — `!{e['command']}` {e['detail'][:50]}"
            for e in entries
        ]
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
            "`!deletequote <id>` `!setqotd #channel`",
            inline=False)
        embed.add_field(name="⚙️ Setup", value=
            "`!setup` `!status` `!setquoteboard` `!setechofeed`\n"
            "`!setquoterole` `!setquotestream` `!setwelcome` `!quotestop` `!quotestart`",
            inline=False)
        embed.add_field(name="📊 Stats", value=
            "`!quoteboardstats` `!ping` `!auditlog`",
            inline=False)
        embed.add_field(name="👤 Pinned Users", value=
            "`!pinuser @user` `!unpinuser @user` `!pinnedusers`",
            inline=False)
        embed.add_field(name="🔒 Lockdown", value=
            "`!lockdown channel/user/role/server [duration]`\n"
            "`!unlock channel/user/role/server`",
            inline=False)
        embed.add_field(name="🛠️ Admin", value=
            "`!resetquotes` `!exportquotes` `!auditlog`",
            inline=False)
        embed.add_field(name="🎉 Fun", value=
            "`!poll \"question\" \"opt1\" \"opt2\" [duration]`",
            inline=False)
        embed.set_footer(text="Slash command versions available via /")
        await ctx.send(embed=embed)

    # ── /setup slash command ──────────────────────────────────

    @app_commands.command(name="setup", description="Configure the bot using a form")
    @app_commands.default_permissions(administrator=True)
    async def slash_setup(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetupModal())

    # ── /status slash command ─────────────────────────────────

    @app_commands.command(name="status", description="Show current bot configuration")
    @app_commands.default_permissions(administrator=True)
    async def slash_status(self, interaction: discord.Interaction):
        board_id = config.get("quoteboard_channel")
        feed_id = config.get("echo_feed_channel")
        interval = config.get("quote_interval", 30)
        pinned = config.get("pinned_users", {})
        saved = config.get("saved_quotes", [])
        role_id = config.get("quotesave_role")

        embed = discord.Embed(title="📊 Lamarque Bot Status", color=discord.Color.blurple())
        embed.add_field(name="Quoteboard", value=f"<#{board_id}>" if board_id else "❌ Not set", inline=True)
        embed.add_field(name="Echo Feed", value=f"<#{feed_id}>" if feed_id else "❌ Not set", inline=True)
        embed.add_field(name="Feed Interval", value=f"{interval} minutes", inline=True)
        embed.add_field(name="Quotes Saved", value=str(len(saved)), inline=True)
        embed.add_field(name="Pinned Users", value=str(len(pinned)), inline=True)
        embed.add_field(name="Quote Role", value=f"<@&{role_id}>" if role_id else "Everyone", inline=True)
        embed.set_footer(text=f"Latency: {round(self.bot.latency * 1000)}ms")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Setup launch view (button that opens modal) ───────────────

class SetupLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Open Setup Form", style=discord.ButtonStyle.primary, emoji="🔧")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal())


async def setup(bot):
    await bot.add_cog(Admin(bot))
