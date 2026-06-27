import discord
from discord import app_commands, Poll, PollMedia
from discord.ext import commands
from datetime import timedelta


class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, question: str, *args):
        """
        Create a native Discord poll with up to 10 options.
        Usage: !poll "Question?" "Option 1" "Option 2" [duration]
        Duration examples: 1d, 12h, 30m (default: 1d)
        Last argument is treated as duration if it matches the format.
        """
        if not args:
            await ctx.send(
                "❌ Usage: `!poll \"Question?\" \"Option 1\" \"Option 2\" [duration]`\n"
                "Duration examples: `1d`, `12h`, `30m`",
                delete_after=10
            )
            return

        options = list(args)
        duration_hours = 24  # default 1 day

        # check if last arg is a duration
        last = options[-1]
        try:
            if last.endswith("d"):
                duration_hours = int(last[:-1]) * 24
                options = options[:-1]
            elif last.endswith("h"):
                duration_hours = int(last[:-1])
                options = options[:-1]
            elif last.endswith("m"):
                duration_hours = max(1, int(last[:-1]) // 60)
                options = options[:-1]
        except ValueError:
            pass

        if len(options) < 2:
            await ctx.send("❌ You need at least 2 options.", delete_after=5)
            return

        if len(options) > 10:
            await ctx.send("❌ Maximum 10 options.", delete_after=5)
            return

        poll = Poll(
            question=PollMedia(text=question),
            duration=timedelta(hours=duration_hours),
            multiple=False
        )

        for option in options:
            poll.add_answer(text=option)

        await ctx.send(poll=poll)
        await ctx.message.delete()

    @app_commands.command(name="poll", description="Create a native Discord poll with up to 10 options")
    @app_commands.describe(
        question="The poll question",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3 (optional)",
        option4="Option 4 (optional)",
        option5="Option 5 (optional)",
        option6="Option 6 (optional)",
        option7="Option 7 (optional)",
        option8="Option 8 (optional)",
        option9="Option 9 (optional)",
        option10="Option 10 (optional)",
        duration="Duration e.g. 1d, 12h, 30m (default: 1d)"
    )
    async def slash_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
        option6: str = None,
        option7: str = None,
        option8: str = None,
        option9: str = None,
        option10: str = None,
        duration: str = "1d"
    ):
        options = [o for o in [option1, option2, option3, option4, option5,
                                option6, option7, option8, option9, option10] if o]

        duration_hours = 24
        try:
            if duration.endswith("d"):
                duration_hours = int(duration[:-1]) * 24
            elif duration.endswith("h"):
                duration_hours = int(duration[:-1])
            elif duration.endswith("m"):
                duration_hours = max(1, int(duration[:-1]) // 60)
        except ValueError:
            pass

        poll = Poll(
            question=PollMedia(text=question),
            duration=timedelta(hours=duration_hours),
            multiple=False
        )

        for option in options:
            poll.add_answer(text=option)

        await interaction.response.send_message(poll=poll)


async def setup(bot):
    await bot.add_cog(PollCog(bot))
