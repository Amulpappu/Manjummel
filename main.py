import asyncio
import logging
import discord
from discord.ext import commands
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ManjummelBot")

# Configure Intents (All intents enabled for Moderation, Invites & Voice)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.invites = True

bot = commands.Bot(
    command_prefix=config.COMMAND_PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

INITIAL_COGS = [
    "cogs.general",
    "cogs.birthday",
    "cogs.youtube",
    "cogs.music",
    "cogs.invite_tracker",
    "cogs.moderation",
    "cogs.logging",
]


@bot.event
async def on_ready():
    logger.info(f"👑 Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🤖 Connected to {len(bot.guilds)} server(s).")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{config.COMMAND_PREFIX}help | Manjummel Bot"
        )
    )

async def main():
    async with bot:
        for cog in INITIAL_COGS:
            try:
                await bot.load_extension(cog)
                logger.info(f"✅ Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog}: {e}")

        if not config.DISCORD_TOKEN or config.DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
            logger.error("❌ DISCORD_TOKEN is missing or invalid! Set DISCORD_TOKEN in config.py or .env")
            return

        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user.")
