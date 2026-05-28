import asyncio
import logging
import os
import time

from dotenv import load_dotenv
import fluxer

load_dotenv()

TOKEN = os.environ["FLUXER_BOT_TOKEN"]
PREFIX = os.getenv("PREFIX", "!")

_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(
    level=_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")

intents = fluxer.Intents.all()
bot = fluxer.Bot(command_prefix=PREFIX, intents=intents)
bot.launch_time = time.monotonic()

# remove built-in help if one is injected by default
try:
    bot.remove_command("help")
except Exception:
    pass


@bot.event
async def on_ready():
    print(f"[ready] {bot.user.username} ({bot.user.id}) | prefix={PREFIX!r}")


@bot.event
async def on_command_error(ctx, error):
    name = type(error).__name__
    if any(k in name for k in ("Permission", "Check", "Missing", "Forbidden")):
        await ctx.channel.send("You don't have permission to use that command.")
        return
    if "NotFound" in name or "CommandNotFound" in name:
        return
    log.exception("Unhandled command error in %r", getattr(ctx, "message", None), exc_info=error)


@bot.event
async def on_error(event_name: str, *args, **kwargs):
    log.exception("Error in event %s", event_name)


COGS = ["cog_moderation", "cog_utility", "cog_fun"]


async def load_cogs():
    for name in COGS:
        await bot.load_extension(name)
        log.info("loaded %s", name)


asyncio.run(load_cogs())
bot.run(TOKEN)
