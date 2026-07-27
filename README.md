# Manjummel - All-Rounder Discord Bot 🤖🎵🎂🔴

**Manjummel** is a feature-rich, modular Discord bot built with `discord.py` (v2.x).

---

## 🌟 Key Features

1. **🎵 Music Player (Flavia style):**
   - Play music from YouTube directly into Discord voice channels with interactive UI buttons.
   - Commands: `!play <song/URL>`, `!pause`, `!resume`, `!skip`, `!stop`, `!shuffle`, `!queue`, `!leave`.

2. **🌸 Welcome Cards (Koya style):**
   - Welcomes new users with avatar thumbnails, account creation age, and join position badges.

3. **📩 Invite Tracker (Invite Tracker style):**
   - Caches invites and tracks real vs fake vs left invite statistics.
   - Commands: `!invites [@user]`, `!invitesleaderboard`.

4. **🛡️ Moderation & Server Stats (ProBot / Carl / StatBot style):**
   - Full moderation suite (`!warn`, `!warns`, `!clearwarns`, `!kick`, `!ban`, `!purge`).
   - Audit logging for deleted and edited messages.
   - Server & user profile analytics (`!serverinfo`, `!userinfo`).

5. **🎂 Birthday Tracker & Star Role (WishWave style):**
   - Users can register their birthdays (`!setbirthday MM-DD`, `!setbirthdaymsg`).
   - Automated daily task checks for birthdays and assigns temporary `@Birthday Star` role.
   - Commands: `!setbirthday`, `!setbirthdaymsg`, `!setbirthdayrole`, `!listbirthdays`.

6. **🔴 YouTube Live & Video Alerts:**
   - Automatic RSS-feed tracking for YouTube channels (no API key required).
   - Automatically posts custom embeds and role pings (`!setytrole`) when a video or live stream goes live.
   - Commands: `!addyt <UC_CHANNEL_ID>`, `!setytrole @Role`.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- `ffmpeg` installed on your system PATH (required for Music playback).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file inside the directory:
```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=!
ANNOUNCEMENT_CHANNEL_ID=your_channel_id_here
WELCOME_CHANNEL_ID=your_welcome_channel_id_here
```

### 4. Run the Bot
```bash
python main.py
```
