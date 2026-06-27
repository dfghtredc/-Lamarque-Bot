import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config_manager import init_db, close_db

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable not set.")

# ── Logging setup ─────────────────────────────────────────────
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(handler)
log.addHandler(logging.StreamHandler())

# ── Bot setup ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

COGS = [
    "cogs.security",
    "cogs.lockdown",
    "cogs.welcome",
    "cogs.antispam",
    "cogs.poll",
    "cogs.admin",
    "cogs.quoteboard",
]

GUILD_ID = 1519789669250891807
TEST_BOT_ID = 1520264910523727953


@bot.event
async def on_ready():
    logging.info(f"[BOT] Logged in as {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logging.info("[SLASH] Guild commands synced")
    await bot.tree.sync()
    logging.info("[SLASH] Global commands synced")


@bot.event
async def on_disconnect():
    logging.warning("[BOT] Disconnected from Discord.")


@bot.event
async def on_message(message):
    # allow test runner bot to trigger commands
    # block all other bots
    if message.author.bot and message.author.id != TEST_BOT_ID:
        return
    await bot.process_commands(message)


async def main():
    await init_db()
    logging.info("[DB] Database initialized")

    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                logging.info(f"[COGS] Loaded {cog}")
            except Exception as e:
                logging.error(f"[COGS] Failed to load {cog}: {e}")

        try:
            await bot.start(TOKEN)
        finally:
            await close_db()
            logging.info("[DB] Database closed")


asyncio.run(main())
