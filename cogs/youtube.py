import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import json
import os
import re
import config

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOUTUBERS_FILE = os.path.join(DATA_DIR, "youtubers.json")

def load_youtubers():
    if os.path.exists(YOUTUBERS_FILE):
        try:
            with open(YOUTUBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default configuration with user's YouTube channel @AMULPAPPU_001
    default_data = {
        "ping_role": "family",
        "youtubers": [
            {
                "handle": "@AMULPAPPU_001",
                "channel_id": "UCIkCNsY2HDPAeAxL_I3hDNw",
                "name": "AMULPAPPU 001",
                "ping_enabled": True,
                "url": "https://www.youtube.com/@AMULPAPPU_001",
                "last_video_id": ""
            }
        ]
    }
    save_youtubers(default_data)
    return default_data

def save_youtubers(data):
    with open(YOUTUBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

async def resolve_channel_id(handle_or_url: str):
    """Resolves a YouTube handle, URL, or ID into a valid YouTube Channel ID."""
    clean = handle_or_url.strip()
    if clean.startswith("UC") and len(clean) == 24 and " " not in clean:
        return clean, clean
    
    if not clean.startswith("http"):
        handle = clean if clean.startswith("@") else f"@{clean}"
        url = f"https://www.youtube.com/{handle}"
    else:
        url = clean

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'<meta itemprop="channelId" content="([^"]+)"', html)
                    if match:
                        return match.group(1), url
                    
                    match = re.search(r'https://www\.youtube\.com/feeds/videos\.xml\?channel_id=([^"]+)', html)
                    if match:
                        return match.group(1), url

                    match = re.search(r'"browseId":"(UC[^"]+)"', html)
                    if match:
                        return match.group(1), url
        except Exception as e:
            print(f"[YouTube Resolve Error] {e}")
    return None, url

class YouTube(commands.Cog):
    """YouTube Live Stream Auto-Notifier & Self-Promotion Monitor for Manjummel Bot."""

    def __init__(self, bot):
        self.bot = bot
        self.data = load_youtubers()
        self.yt_check_loop.start()

    def cog_unload(self):
        self.yt_check_loop.cancel()

    def get_promo_channel(self, guild: discord.Guild):
        """Finds self-promotion channel by name (fuzzy match)."""
        for channel in guild.text_channels:
            name_clean = channel.name.lower().replace("📻┆", "").replace("-", "_")
            if "self_promotion" in name_clean or "selfpromotion" in name_clean or "promo" in name_clean:
                return channel
        return None

    def get_ping_role(self, guild: discord.Guild):
        """Finds @family role in guild."""
        role_name = self.data.get("ping_role", "family")
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            for r in guild.roles:
                if role_name.lower() in r.name.lower():
                    return r
        return role

    @commands.command(name="addyoutuber", aliases=["addytuber"])
    @commands.has_permissions(administrator=True)
    async def add_youtuber(self, ctx, handle_or_url: str, *, custom_name: str = ""):
        """Adds a YouTuber to auto-ping @family when live. Usage: !addyoutuber @AMULPAPPU_001 [Name]"""
        async with ctx.typing():
            channel_id, full_url = await resolve_channel_id(handle_or_url)
            if not channel_id:
                return await ctx.send(f"❌ Could not resolve YouTube Channel ID for `{handle_or_url}`. Please verify handle/URL.")
            
            # Check if already added
            youtubers = self.data.get("youtubers", [])
            for y in youtubers:
                if y.get("channel_id") == channel_id:
                    return await ctx.send(f"⚠️ YouTuber **{y.get('name')}** (`{channel_id}`) is already registered!")

            name = custom_name or handle_or_url.replace("https://www.youtube.com/", "").replace("https://youtu.be/", "")
            new_entry = {
                "handle": handle_or_url if handle_or_url.startswith("@") else f"@{name}",
                "channel_id": channel_id,
                "name": name,
                "ping_enabled": True,
                "url": full_url,
                "last_video_id": ""
            }
            youtubers.append(new_entry)
            self.data["youtubers"] = youtubers
            save_youtubers(self.data)

            await ctx.send(f"✅ Added YouTuber **{name}** (`{channel_id}`)! Will auto-ping `@family` in `#📻┆ꜱᴇʟꜰ-ᴘʀᴏᴍᴏᴛɪᴏɴ` when live!")

    @commands.command(name="listyoutubers", aliases=["listytubers"])
    async def list_youtubers(self, ctx):
        """Lists all registered YouTubers."""
        youtubers = self.data.get("youtubers", [])
        if not youtubers:
            return await ctx.send("📜 No YouTubers registered yet. Use `!addyoutuber @handle` to add one.")
        
        embed = discord.Embed(
            title="📺 Registered YouTubers (Auto-Ping @family)",
            color=discord.Color.red()
        )
        for idx, y in enumerate(youtubers, 1):
            status = "🟢 Ping @family Enabled" if y.get("ping_enabled", True) else "⚪ Ping Disabled"
            embed.add_field(
                name=f"{idx}. {y.get('name')} ({y.get('handle')})",
                value=f"**Channel ID:** `{y.get('channel_id')}`\n**Status:** {status}\n[Channel Link]({y.get('url')})",
                inline=False
            )
        await ctx.send(embed=embed)

    # ── Self-Promotion Channel Link Listener ───────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        promo_ch = self.get_promo_channel(message.guild)
        if promo_ch and message.channel.id == promo_ch.id:
            # Check if message contains YouTube link
            urls = re.findall(r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+)', message.content)
            if urls:
                target_url = urls[0]
                youtubers = self.data.get("youtubers", [])
                matched_yt = None
                video_title = "Live Stream / Video"

                # 1. Fetch YouTube oEmbed to get channel author_name & author_url
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
                oembed_api = f"https://www.youtube.com/oembed?url={target_url}&format=json"

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(oembed_api, headers=headers, timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                author_name = data.get("author_name", "")
                                author_url = data.get("author_url", "")
                                video_title = data.get("title", video_title)

                                for y in youtubers:
                                    y_cid = y.get("channel_id", "").lower()
                                    y_handle = y.get("handle", "").lower().replace("@", "")
                                    y_url = y.get("url", "").lower()

                                    if (y_url and y_url in author_url.lower()) or (y_handle and y_handle in author_url.lower()) or (y_cid and y_cid in target_url.lower()):
                                        matched_yt = y
                                        break
                except Exception as e:
                    print(f"[YouTube oEmbed Error] {e}")

                # 2. Fallback: Match if message author is Server Owner / Admin or matches handle
                if not matched_yt:
                    is_admin_or_owner = message.author.id == message.guild.owner_id or message.author.guild_permissions.administrator
                    for y in youtubers:
                        h = y.get("handle", "").lower().replace("@", "")
                        n = y.get("name", "").lower()
                        if h and (h in message.author.name.lower() or h in message.author.display_name.lower() or n in message.author.display_name.lower()):
                            matched_yt = y
                            break
                    if not matched_yt and is_admin_or_owner and youtubers:
                        # Default to first registered YouTuber if posted by Server Owner/Admin
                        matched_yt = youtubers[0]

                # 3. If REGISTERED YouTuber or Admin: Delete user message & post official bot live alert!
                if matched_yt and matched_yt.get("ping_enabled", True):
                    # Delete the user's raw message so only the bot announcement remains
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"[Self-Promo] Could not delete user message: {e}")

                    ping_role = self.get_ping_role(message.guild)
                    role_mention = ping_role.mention if ping_role else "@family"
                    streamer_name = matched_yt.get('name', 'AMULPAPPU 001')

                    content_text = (
                        f"🔴 {role_mention} **{streamer_name} IS LIVE!**\n"
                        f"🎬 **[{video_title}]({target_url})**\n"
                        f"👉 **[Click Here to Watch Stream]({target_url})**"
                    )

                    embed = discord.Embed(
                        title=f"🔴 {streamer_name} IS LIVE!",
                        description=f"🎬 **[{video_title}]({target_url})**\n\n👉 **[Click Here to Watch Stream]({target_url})**",
                        color=discord.Color.red(),
                        url=target_url
                    )
                    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                    embed.set_footer(text="Manjummel Live Stream Alert", icon_url="https://www.youtube.com/s/desktop/f71fb147/img/favicon.ico")

                    await message.channel.send(content=content_text, embed=embed)
                else:
                    # NOT REGISTERED: Allow link in self-promotion, but NO PING @family!
                    print(f"[Self-Promo] Unregistered live link posted by {message.author.display_name} - No @family ping.")

    # ── Automated RSS Stream Check Loop ────────────────────────
    @tasks.loop(seconds=60)
    async def yt_check_loop(self):
        """Periodically checks YouTube RSS feeds for registered channels."""
        await self.bot.wait_until_ready()
        youtubers = self.data.get("youtubers", [])
        if not youtubers:
            return

        async with aiohttp.ClientSession() as session:
            for y in youtubers:
                ch_id = y.get("channel_id")
                if not ch_id:
                    continue

                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch_id}"
                try:
                    async with session.get(rss_url, timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        xml_data = await resp.text()

                    root = ET.fromstring(xml_data)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

                    entries = root.findall("atom:entry", ns)
                    if entries:
                        latest_entry = entries[0]  # Newest video
                        video_id = latest_entry.find("yt:videoId", ns).text
                        title = latest_entry.find("atom:title", ns).text
                        link = latest_entry.find("atom:link", ns).attrib["href"]

                        last_id = y.get("last_video_id", "")
                        if video_id and video_id != last_id:
                            y["last_video_id"] = video_id
                            save_youtubers(self.data)

                            # Announce live stream / video to all guilds
                            for guild in self.bot.guilds:
                                promo_ch = self.get_promo_channel(guild)
                                if promo_ch:
                                    ping_role = self.get_ping_role(guild)
                                    role_str = ping_role.mention if (ping_role and y.get("ping_enabled", True)) else "@family"

                                    embed = discord.Embed(
                                        title=f"🎬 {title}",
                                        description=f"🔴 **{y.get('name')}** is NOW LIVE or uploaded a new video!\n\n👉 **[Watch on YouTube]({link})**",
                                        color=discord.Color.red(),
                                        url=link
                                    )
                                    embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
                                    embed.set_footer(text="Manjummel YouTube Alert")

                                    msg_text = f"🔴 {role_str} **{y.get('name')}** IS NOW LIVE!" if y.get("ping_enabled", True) else f"📹 **{y.get('name')}** posted a video!"
                                    await promo_ch.send(content=msg_text, embed=embed)
                except Exception as e:
                    print(f"[YouTube Loop Error] Channel {ch_id}: {e}")

    @yt_check_loop.before_loop
    async def before_yt_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTube(bot))
