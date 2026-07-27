import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import json
import os
import re
import config

class YouTube(commands.Cog):
    """Cog for automatically monitoring and announcing YouTube videos & live streams with role pings."""

    def __init__(self, bot):
        self.bot = bot
        self.posted_videos = self.load_posted_state()
        self.yt_config = self.load_yt_config()
        self.channels = self.load_channels()
        self.yt_check_loop.start()

    def cog_unload(self):
        self.yt_check_loop.cancel()

    def load_posted_state(self):
        if os.path.exists(config.YT_FEED_FILE):
            try:
                with open(config.YT_FEED_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def save_posted_state(self):
        with open(config.YT_FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self.posted_videos), f, indent=4)

    def load_yt_config(self):
        if os.path.exists(config.YT_CONFIG_FILE):
            try:
                with open(config.YT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_yt_config(self):
        with open(config.YT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.yt_config, f, indent=4)

    def load_channels(self):
        channels = self.yt_config.get("channels", [])
        if config.YOUTUBE_CHANNEL_ID and config.YOUTUBE_CHANNEL_ID not in channels:
            channels.append(config.YOUTUBE_CHANNEL_ID)
        return channels

    @commands.command(name="addyt")
    @commands.has_permissions(administrator=True)
    async def add_yt_channel(self, ctx, channel_id: str):
        """Adds a YouTube Channel ID to track for live/video announcements. Usage: !addyt UCxxxxxxxx"""
        if channel_id in self.channels:
            await ctx.send(f"⚠️ YouTube Channel `{channel_id}` is already being tracked.")
            return
        self.channels.append(channel_id)
        self.yt_config["channels"] = self.channels
        self.save_yt_config()
        await ctx.send(f"✅ Added YouTube Channel `{channel_id}` to automated stream & video alerts!")

    @commands.command(name="setytrole")
    @commands.has_permissions(administrator=True)
    async def set_yt_role(self, ctx, role: discord.Role):
        """Sets the specific role to ping when a YouTube video or live stream is posted. Usage: !setytrole @StreamPing"""
        self.yt_config["ping_role_id"] = role.id
        self.save_yt_config()
        await ctx.send(f"✅ YouTube Live & Video alerts will now ping role **{role.name}** (`{role.id}`)!")

    @tasks.loop(seconds=config.YOUTUBE_CHECK_INTERVAL_SECONDS)
    async def yt_check_loop(self):
        """Periodically checks tracked YouTube channels via RSS feeds."""
        await self.bot.wait_until_ready()
        if not self.channels:
            return

        async with aiohttp.ClientSession() as session:
            for ch_id in self.channels:
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch_id}"
                try:
                    async with session.get(rss_url, timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        xml_data = await resp.text()
                        
                    root = ET.fromstring(xml_data)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
                    
                    entries = root.findall("atom:entry", ns)
                    for entry in reversed(entries):  # Process oldest to newest
                        video_id = entry.find("yt:videoId", ns).text
                        title = entry.find("atom:title", ns).text
                        link = entry.find("atom:link", ns).attrib["href"]
                        author = entry.find("atom:author/atom:name", ns).text

                        if video_id not in self.posted_videos:
                            self.posted_videos.add(video_id)
                            self.save_posted_state()

                            # Post announcement to Discord
                            await self.announce_video(author, title, link, video_id)
                except Exception as e:
                    print(f"[YouTube Cog Error] Failed checking channel {ch_id}: {e}")

    async def announce_video(self, author_name: str, title: str, link: str, video_id: str = ""):
        """Posts YouTube video/live stream link with rich embed display and role pinging."""
        for guild in self.bot.guilds:
            ch_id = config.ANNOUNCEMENT_CHANNEL_ID or config.WELCOME_CHANNEL_ID
            channel = guild.get_channel(ch_id) if ch_id else guild.system_channel
            if channel:
                # Determine role ping
                role_ping_str = "@everyone"
                ping_role_id = self.yt_config.get("ping_role_id") or config.YOUTUBE_PING_ROLE_ID
                if ping_role_id:
                    role = guild.get_role(int(ping_role_id))
                    if role:
                        role_ping_str = role.mention
                    else:
                        role_ping_str = f"<@&{ping_role_id}>"

                content_msg = f"🔴 {role_ping_str} **{author_name}** is live / posted a new YouTube video!"
                
                embed = discord.Embed(
                    title=f"🎬 {title}",
                    description=f"**{author_name}** just went live or uploaded a new video!\n\n👉 **[Click Here to Watch on YouTube]({link})**",
                    color=discord.Color.red(),
                    url=link
                )
                if video_id:
                    embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
                
                embed.add_field(name="Channel", value=f"**{author_name}**", inline=True)
                embed.add_field(name="Watch Link", value=f"[Watch Video]({link})", inline=True)
                embed.set_footer(text="Manjummel YouTube Live Alert", icon_url="https://www.youtube.com/s/desktop/f71fb147/img/favicon.ico")
                
                await channel.send(content=content_msg, embed=embed)



    @yt_check_loop.before_loop
    async def before_yt_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTube(bot))

