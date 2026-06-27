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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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


async def main():
    # init database and load config into memory before anything else
    await init_db()
    print("[DB] Database initialized")

    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"[COGS] Loaded {cog}")
            except Exception as e:
                print(f"[COGS] Failed to load {cog}: {e}")

        try:
            await bot.start(TOKEN)
        finally:
            await close_db()
            print("[DB] Database closed")


@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user}")

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print("[SLASH] Guild commands synced")

    await bot.tree.sync()
    print("[SLASH] Global commands synced")


@bot.event
async def on_disconnect():
    print("[BOT] Disconnected from Discord.")


handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

if __name__ == "__main__":
    logging.basicConfig(handlers=[handler], level=logging.INFO)
    asyncio.run(main())
