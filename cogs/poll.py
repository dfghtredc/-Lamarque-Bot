import discord
from discord.ext import commands

NUMBER_EMOJIS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, question: str, *options: str):
        """
        Create a poll with up to 10 options.
        Usage: !poll "Question?" "Option 1" "Option 2" ...
        """
        if len(options) < 2:
            await ctx.send("❌ You need at least 2 options.", delete_after=5)
            return

        if len(options) > 10:
            await ctx.send("❌ Maximum 10 options.", delete_after=5)
            return

        description = "\n".join(
            f"{NUMBER_EMOJIS[i]} {option}"
            for i, option in enumerate(options)
        )

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        poll_msg = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_msg.add_reaction(NUMBER_EMOJIS[i])

        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Poll(bot))
