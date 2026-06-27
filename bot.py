import os
import asyncio
import logging
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config_manager import load_config

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
    "cogs.quoteboard",
]

GUILD_ID = 1519789669250891807

async def main():
    # load config into memory before anything else
    load_config()

    async with bot:
        # load all cogs before connecting
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"[COGS] Loaded {cog}")
            except Exception as e:
                print(f"[COGS] Failed to load {cog}: {e}")

        await bot.start(TOKEN)


@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user}")

    # guild sync — instant
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print("[SLASH] Guild commands synced")

    # global sync — up to 1 hour
    await bot.tree.sync()
    print("[SLASH] Global commands synced")


@bot.event
async def on_disconnect():
    print("[BOT] Disconnected from Discord.")


handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

if __name__ == "__main__":
    logging.basicConfig(
        handlers=[handler],
        level=logging.INFO
    )
    asyncio.run(main())
