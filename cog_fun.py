import random
import re

import fluxer
from fluxer import Cog

BALL_RESPONSES = [
    # positive
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    # neutral
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    # negative
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
]


class Fun(Cog):
    def __init__(self, bot: fluxer.Bot):
        self.bot = bot
        super().__init__()

    # -------------------------------------------------------------------------
    # 8ball
    # -------------------------------------------------------------------------
    @Cog.command(name="8ball")
    async def eightball(self, ctx, *, question: str):
        await ctx.channel.send(f"🎱 {random.choice(BALL_RESPONSES)}")

    # -------------------------------------------------------------------------
    # coinflip
    # -------------------------------------------------------------------------
    @Cog.command(name="coinflip")
    async def coinflip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        coin = "🪙"
        await ctx.channel.send(f"{coin} **{result}**")

    # -------------------------------------------------------------------------
    # roll  -- NdN dice notation, e.g. !roll 2d20
    # -------------------------------------------------------------------------
    @Cog.command(name="roll")
    async def roll(self, ctx, dice: str = "1d6"):
        match = re.fullmatch(r"(\d{1,2})d(\d{1,4})", dice.lower())
        if not match:
            await ctx.channel.send("Usage: `!roll NdN` e.g. `!roll 2d20`")
            return
        count, sides = int(match.group(1)), int(match.group(2))
        if count < 1 or sides < 2:
            await ctx.channel.send("Count must be >= 1 and sides >= 2.")
            return
        if count > 25:
            await ctx.channel.send("Max 25 dice at once.")
            return
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        if count == 1:
            await ctx.channel.send(f"🎲 **{total}**")
        else:
            breakdown = " + ".join(str(r) for r in rolls)
            await ctx.channel.send(f"🎲 {breakdown} = **{total}**")

    # -------------------------------------------------------------------------
    # choose  -- pick one option from a pipe-separated list
    # -------------------------------------------------------------------------
    @Cog.command(name="choose")
    async def choose(self, ctx, *, options: str):
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            await ctx.channel.send("Provide at least 2 options separated by `|`.")
            return
        picked = random.choice(choices)
        await ctx.channel.send(f"I choose: **{picked}**")

    # -------------------------------------------------------------------------
    # reverse  -- reverse a string
    # -------------------------------------------------------------------------
    @Cog.command(name="reverse")
    async def reverse(self, ctx, *, text: str):
        await ctx.channel.send(text[::-1])

    # -------------------------------------------------------------------------
    # mock  -- alternating case (SpOnGeBoB meme)
    # -------------------------------------------------------------------------
    @Cog.command(name="mock")
    async def mock(self, ctx, *, text: str):
        result = "".join(
            c.upper() if i % 2 == 0 else c.lower()
            for i, c in enumerate(text)
        )
        await ctx.channel.send(result)


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Fun(bot))
