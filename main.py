import os
import sys

# Force immediate unbuffered logging for Render live console output
os.environ["PYTHONUNBUFFERED"] = "1"
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

import threading
import asyncio
import logging
import discord
from discord.ext import commands
from flask import Flask
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ManjummelBot")

# ── Render HTTP Port Binding Web Server ────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>🤖 Manjummel Bot is Online 24/7!</h1><p>Status: Active & Operational</p>"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting Web Server for Render Port Binding on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ── Discord Bot Setup ─────────────────────────────────────
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
    logger.info(f"👑 LOGGED IN SUCCESSFULLY as {bot.user} (ID: {bot.user.id})")
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
                logger.error(f"❌ Failed to load cog {cog}: {e}", exc_info=True)

        token = config.DISCORD_TOKEN
        if not token or token == "YOUR_DISCORD_BOT_TOKEN":
            logger.error("❌ DISCORD_TOKEN is missing! Please set DISCORD_TOKEN in Render Environment Variables.")
            return

        try:
            logger.info("🔑 Connecting to Discord Gateway API...")
            await bot.start(token)
        except discord.LoginFailure:
            logger.error("❌ DISCORD LOGIN FAILURE: Improper or Invalid Bot Token provided!")
        except Exception as e:
            logger.error(f"❌ DISCORD LOGIN FAILED: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        # Start background web server for Render port binding
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()

        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user.")
