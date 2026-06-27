"""
helpers.py — sync utilities (no I/O)
async_helpers logic is handled in quote_cache and config_manager directly.
"""
import discord
from config_manager import config, save_config, add_saved_quote, is_saved
from quote_cache import quote_cache
from cogs.security import can_use_command


def build_embed(msg: discord.Message, search_channel: discord.TextChannel, action_by: str) -> discord.Embed:
    embed = discord.Embed(
        description=msg.content,
        color=discord.Color.gold(),
        timestamp=msg.created_at
    )
    embed.set_author(
        name=msg.author.display_name,
        icon_url=msg.author.display_avatar.url
    )
    # store author ID in footer for reliable stat lookups
    embed.set_footer(text=f"#{search_channel.name} · {action_by} · uid:{msg.author.id}")
    if msg.attachments:
        embed.set_image(url=msg.attachments[0].url)
    return embed


async def save_to_quoteboard(bot, msg: discord.Message, channel: discord.TextChannel, action_by: str):
    """
    Save a message to the quoteboard channel.
    Returns the sent embed message, or None if already saved or unavailable.
    """
    board_id = config.get("quoteboard_channel")
    if not board_id:
        return None

    if is_saved(msg.id):
        return None

    board_channel = bot.get_channel(board_id)
    if not board_channel:
        return None

    # guild scope check — prevent cross-guild channel access
    if board_channel.guild.id != channel.guild.id:
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
        except (discord.NotFound, discord.HTTPException):
            pass

    sent = await board_channel.send(embed=embed)

    # update in-memory config and persist
    add_saved_quote(msg.id)

    # invalidate quote cache so next fetch includes this quote
    await quote_cache.invalidate()

    return sent


async def get_random_quote(bot, prioritize_pinned: bool = False):
    """
    Get a random quote from the quoteboard using the cache.
    """
    board_id = config.get("quoteboard_channel")
    if not board_id:
        return None

    pinned_names = None
    if prioritize_pinned:
        pinned = config.get("pinned_users", {})
        channel = bot.get_channel(board_id)
        if channel and pinned:
            pinned_names = []
            for uid in pinned.keys():
                member = channel.guild.get_member(int(uid))
                if member:
                    pinned_names.append(member.display_name)

    return await quote_cache.get_random(bot, board_id, pinned_names)
