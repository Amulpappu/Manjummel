import os
import sys

# Force immediate unbuffered UTF-8 logging output
os.environ["PYTHONUNBUFFERED"] = "1"
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import threading
import asyncio

import logging
import discord
from discord.ext import commands
from flask import Flask
import config

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging without emoji encoding issues
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ManjummelBot")

from flask import render_template, request, jsonify
from cogs.youtube import load_youtubers, save_youtubers, resolve_channel_id

# ── Render HTTP Port Binding Web Server & YouTuber Dashboard ──
app = Flask(__name__, template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/youtubers")
def youtubers_dashboard():
    data = load_youtubers()
    return render_template("youtubers.html", youtubers=data.get("youtubers", []), ping_role=data.get("ping_role", "family"))

@app.route("/api/youtubers/add", methods=["POST"])
def api_add_youtuber():
    req_data = request.get_json() or {}
    handle = req_data.get("handle", "").strip()
    name = req_data.get("name", "").strip()

    if not handle:
        return jsonify({"success": False, "message": "Handle or Channel URL is required."})

    data = load_youtubers()
    # Resolve channel ID asynchronously in loop or sync helper
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    channel_id, full_url = loop.run_until_complete(resolve_channel_id(handle))
    loop.close()

    if not channel_id:
        return jsonify({"success": False, "message": f"Could not resolve YouTube Channel ID for {handle}."})

    youtubers = data.get("youtubers", [])
    for y in youtubers:
        if y.get("channel_id") == channel_id:
            return jsonify({"success": False, "message": f"YouTuber {y.get('name')} is already registered!"})

    final_name = name or handle.replace("https://www.youtube.com/", "").replace("https://youtu.be/", "")
    from cogs.youtube import get_latest_video_id
    last_vid = loop.run_until_complete(get_latest_video_id(channel_id))
    new_entry = {
        "handle": handle if handle.startswith("@") else f"@{final_name}",
        "channel_id": channel_id,
        "name": final_name,
        "ping_enabled": True,
        "url": full_url,
        "last_video_id": last_vid
    }
    youtubers.append(new_entry)
    data["youtubers"] = youtubers
    save_youtubers(data)

    return jsonify({"success": True, "message": f"Added YouTuber {final_name}!", "entry": new_entry})

@app.route("/api/youtubers/delete/<channel_id>", methods=["POST"])
def api_delete_youtuber(channel_id):
    data = load_youtubers()
    youtubers = data.get("youtubers", [])
    data["youtubers"] = [y for y in youtubers if y.get("channel_id") != channel_id]
    save_youtubers(data)
    return jsonify({"success": True, "message": "Deleted YouTuber."})

WELCOME_CONFIG_FILE = os.path.join(DATA_DIR, "welcome_config.json")

def load_welcome_config():
    if os.path.exists(WELCOME_CONFIG_FILE):
        try:
            with open(WELCOME_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "enabled": True,
        "channel_name": "welcome",
        "server_name": "Manjummel Boys",
        "line2": "Have A Great Time here ❤️",
        "rules_channel": "#📖┆DISCORD-RULES",
        "welcome_title": "WELCOME",
        "welcome_subtitle": "HI GUYS",
        "bg_color": "#0f172a",
        "title_color": "#00e678",
        "name_color": "#ff2d55",
        "auto_role": "family"
    }

def save_welcome_config(data):
    with open(WELCOME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app.route("/welcome")
def welcome_dashboard():
    try:
        config_data = load_welcome_config()
        return render_template("welcome.html", welcome_config=config_data)
    except Exception as e:
        logger.error(f"[Welcome Dashboard Error] {e}")
        return f"Error loading welcome dashboard: {e}", 500

@app.route("/api/welcome/update", methods=["POST"])
def api_update_welcome():
    try:
        new_data = request.json or {}
        save_welcome_config(new_data)
        return jsonify({"success": True, "message": "Updated welcome configuration."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/welcome/test", methods=["POST"])
def api_test_welcome():
    if not bot.loop or not bot.is_ready():
        return jsonify({"success": False, "message": "Bot is starting up. Please wait a few seconds and try again."})

    async def trigger_test():
        welcome_cog = bot.get_cog("Welcome")
        if not welcome_cog:
            return False, "Welcome module is not loaded."

        if not bot.guilds:
            return False, "Bot is not connected to any server."

        guild = bot.guilds[0]
        channel = welcome_cog.get_welcome_channel(guild)
        if not channel:
            return False, "Welcome channel not found."

        member = guild.me
        if guild.members:
            non_bots = [m for m in guild.members if not m.bot]
            if non_bots:
                member = non_bots[0]
            else:
                member = guild.members[0]

        await welcome_cog.send_welcome_message(channel, member)
        return True, f"Test welcome card sent to #{channel.name}!"

    try:
        future = asyncio.run_coroutine_threadsafe(trigger_test(), bot.loop)
        success, message = future.result(timeout=10)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        logger.error(f"[API Test Welcome Error] {e}")
        return jsonify({"success": False, "message": f"Error sending test card: {e}"})

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"[Server] Starting Web Server for Render Port Binding on 0.0.0.0:{port}...")
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
    "cogs.welcome",
    "cogs.youtube",
    "cogs.music",
    "cogs.invite_tracker",
    "cogs.moderation",
    "cogs.logging",
]

@bot.event
async def on_ready():
    logger.info(f"[Bot] LOGGED IN SUCCESSFULLY as {bot.user} (ID: {bot.user.id})")
    logger.info(f"[Bot] Connected to {len(bot.guilds)} server(s).")
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
                logger.info(f"[Cogs] Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"[Cogs Error] Failed to load cog {cog}: {e}")

        token = config.DISCORD_TOKEN
        if not token or token == "YOUR_DISCORD_BOT_TOKEN":
            logger.error("[Auth Error] DISCORD_TOKEN is missing! Set DISCORD_TOKEN in Render Environment Variables.")
            return

        try:
            logger.info("[Auth] Connecting to Discord Gateway API...")
            await bot.start(token)
        except discord.LoginFailure:
            logger.error("[Auth Error] DISCORD LOGIN FAILURE: Improper or Invalid Bot Token provided!")
        except Exception as e:
            logger.error(f"[Auth Error] DISCORD LOGIN FAILED: {e}")

if __name__ == "__main__":
    try:
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()

        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[System] Bot execution interrupted by user.")
