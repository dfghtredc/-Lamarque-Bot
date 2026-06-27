import os
import json
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({}, f)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for cog in ["cogs.lockdown", "cogs.quoteboard"]:
        await bot.load_extension(cog)
        print(f"Loaded {cog}")
    
    # guild sync - instant
    guild = discord.Object(id=1519789669250891807)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print("Guild slash commands synced")

    # global sync - up to 1 hour
    await bot.tree.sync()
    print("Global slash commands synced")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
bot.run(os.getenv("DISCORD_TOKEN"), log_handler=handler, log_level=logging.INFO)