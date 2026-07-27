# Rajan - All-Rounder Discord Bot 🤖🎵🎂🔴

**Rajan** is a feature-rich, modular Discord bot built with `discord.py` (v2.x).

---

## 🌟 Key Features

1. **🎵 Music Player:**
   - Play music from YouTube directly into Discord voice channels (`yt-dlp` powered).
   - Commands: `!play <song/URL>`, `!pause`, `!resume`, `!skip`, `!stop`, `!leave`.

2. **🎂 Birthday Tracker & Announcements:**
   - Users can register their birthdays (`!setbirthday MM-DD`).
   - Automated daily task checks for today's birthdays and sends custom celebration embeds.
   - Commands: `!setbirthday`, `!listbirthdays`.

3. **🔴 YouTube Live & Video Alerts:**
   - Automatic RSS-feed tracking for YouTube channels (no API key required).
   - Automatically posts custom embeds and `@everyone` alerts when a video or live stream goes live.
   - Commands: `!addyt <UC_CHANNEL_ID>`.

4. **🛡️ Moderation & Server Utilities:**
   - Role assignment and removal (`!addrole`, `!removerole`).
   - Automatic welcome embeds when members join.
   - Bot status and latency check (`!ping`, `!botinfo`).

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- `ffmpeg` installed on your system PATH (required for Music playback).

### 2. Install Dependencies
```bash
cd Rajan
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file inside the `Rajan/` directory:
```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=!
ANNOUNCEMENT_CHANNEL_ID=your_channel_id_here
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxx
```

### 4. Run the Bot
```bash
python main.py
```
