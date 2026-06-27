import random
import discord
from utils import load_config, save_config


def can_save_quote(member: discord.Member, config: dict):
    role_id = config.get("quotesave_role")
    if not role_id:
        return True
    return any(r.id == role_id for r in member.roles)


def build_embed(msg, search_channel, action_by):
    embed = discord.Embed(
        description=msg.content,
        color=discord.Color.gold(),
        timestamp=msg.created_at
    )
    embed.set_author(
        name=msg.author.display_name,
        icon_url=msg.author.display_avatar.url
    )
    embed.set_footer(text=f"#{search_channel.name} · {action_by}")
    if msg.attachments:
        embed.set_image(url=msg.attachments[0].url)
    return embed


async def save_to_quoteboard(bot, msg, channel, action_by):
    config = load_config()
    board_id = config.get("quoteboard_channel")
    if not board_id:
        return None

    saved = config.get("saved_quotes", [])
    if msg.id in saved:
        return None

    board_channel = bot.get_channel(board_id)
    if not board_channel:
        return None

    embed = build_embed(msg, channel, action_by)

    if msg.reference:
        try:
            ref_msg = await channel.fetch_message(msg.reference.message_id)
            embed.add_field(
                name=f"Replying to {ref_msg.author.display_name}",
                value=ref_msg.content or "*[no text content]*",
                inline=False
            )
        except discord.NotFound:
            pass

    sent = await board_channel.send(embed=embed)

    saved.append(msg.id)
    config["saved_quotes"] = saved
    save_config(config)

    return sent


async def get_random_quote(bot, prioritize_pinned=False):
    config = load_config()
    board_id = config.get("quoteboard_channel")
    if not board_id:
        return None

    channel = bot.get_channel(board_id)
    if not channel:
        return None

    messages = [
        msg async for msg in channel.history(limit=200)
        if msg.author.bot and msg.embeds
    ]

    if not messages:
        return None

    if prioritize_pinned:
        pinned = config.get("pinned_users", {})
        pinned_names = []
        for uid in pinned.keys():
            member = channel.guild.get_member(int(uid))
            if member:
                pinned_names.append(member.display_name)
        if pinned_names:
            pinned_msgs = [
                msg for msg in messages
                if any(name in msg.embeds[0].author.name for name in pinned_names)
            ]
            if pinned_msgs:
                return random.choice(pinned_msgs)

    return random.choice(messages)
