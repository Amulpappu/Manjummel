import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = DATA_DIR

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    env_file = os.path.join(DATA_DIR, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DISCORD_TOKEN="):
                        DISCORD_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")


# Channel IDs (Optional defaults from environment)
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID", "0"))

# YouTube Monitoring Configuration
# Can specify a channel ID to monitor via RSS feed
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")
YOUTUBE_PING_ROLE_ID = int(os.getenv("YOUTUBE_PING_ROLE_ID", "0"))
YOUTUBE_CHECK_INTERVAL_SECONDS = int(os.getenv("YOUTUBE_CHECK_INTERVAL_SECONDS", "300"))

# Data storage paths
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
BIRTHDAYS_FILE = os.path.join(DATA_DIR, "birthdays.json")
YT_FEED_FILE = os.path.join(DATA_DIR, "youtube_state.json")
YT_CONFIG_FILE = os.path.join(DATA_DIR, "youtube_config.json")

