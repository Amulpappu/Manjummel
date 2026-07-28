import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import aiohttp
import re
import json

async def fetch_spotify_tracks(url: str):
    """Fetches track search terms from Spotify Track, Album, or Playlist URLs."""
    tracks = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with aiohttp.ClientSession() as session:
        if "track" in url:
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            try:
                async with session.get(oembed_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        title = data.get("title", "")
                        if title:
                            tracks.append(title)
            except Exception as e:
                print(f"[Spotify Error] oEmbed fetch failed: {e}")
        elif "playlist" in url or "album" in url:
            spotify_id = url.split("?")[0].split("/")[-1]
            embed_type = "playlist" if "playlist" in url else "album"
            embed_url = f"https://open.spotify.com/embed/{embed_type}/{spotify_id}"
            
            try:
                async with session.get(embed_url, headers=headers) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
                        if match:
                            try:
                                json_data = json.loads(match.group(1))
                                props = json_data.get("props", {}).get("pageProps", {})
                                state = props.get("state", {})
                                entity = state.get("data", {}).get("entity", {}) if isinstance(state, dict) else {}
                                track_list = entity.get("trackList", [])
                                for t in track_list:
                                    t_name = t.get("title", "")
                                    t_artist = t.get("subtitle") or t.get("artists", "")
                                    if t_name:
                                        full_query = f"{t_name} {t_artist}".strip()
                                        if full_query not in tracks:
                                            tracks.append(full_query)
                            except Exception:
                                pass

                        if not tracks:
                            titles = re.findall(r'<meta property="music:song" content="([^"]+)"/>', html)
                            if not titles:
                                titles = re.findall(r'"name":"([^"]+)","track":', html)
                            for t in titles:
                                if t and t not in tracks and len(t) > 2:
                                    tracks.append(t)
            except Exception as e:
                print(f"[Spotify Error] Playlist/Album fetch failed: {e}")

    filtered = []
    for t in tracks:
        if len(t) == 22 and t.isalnum() and " " not in t:
            continue
        filtered.append(t)

    return filtered


YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['tv_embedded', 'android_vr', 'ios', 'android', 'web']
        }
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -headers "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36\r\n"',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

def clean_youtube_url(url: str) -> str:
    """Cleans YouTube URLs by extracting 11-char video ID to strip extra playlist/radio parameters."""
    if "youtube.com" in url or "youtu.be" in url:
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url

async def fetch_video_title_oembed(url: str) -> str:
    """Fetches video title via YouTube oEmbed API for DRM search fallback."""
    clean_url = clean_youtube_url(url)
    oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(oembed_url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("title", "")
    except Exception:
        pass
    return ""

def extract_stream_url(data: dict):
    """Extracts a valid direct HTTP audio stream URL and item dict from yt_dlp data dict."""
    if not data:
        return None, None
    if 'entries' in data and data['entries']:
        valid = [e for e in data['entries'] if e]
        if valid:
            data = valid[0]

    # Direct URL
    url = data.get('url')
    if url and url.startswith("http"):
        return url, data

    formats = data.get('formats', [])

    # Priority 1: Audio-only formats (acodec != 'none' and vcodec == 'none')
    audio_only = [f for f in formats if f.get('acodec') and f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url', '').startswith("http")]
    if audio_only:
        audio_only.sort(key=lambda f: f.get('tbr') or f.get('abr') or 0, reverse=True)
        return audio_only[0]['url'], data

    # Priority 2: Any format with audio (acodec != 'none', e.g. combined MP4/AAC itag 18)
    audio_any = [f for f in formats if f.get('acodec') and f.get('acodec') != 'none' and f.get('url', '').startswith("http")]
    if audio_any:
        return audio_any[0]['url'], data

    # Priority 3: Fallback to any format containing a valid HTTP stream URL
    any_stream = [f for f in formats if f.get('url', '').startswith("http")]
    if any_stream:
        return any_stream[0]['url'], data

    return None, data

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester=None, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown Track')
        self.url = data.get('webpage_url', data.get('url', ''))
        self.stream_url = data.get('url', '')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail', '')
        self.uploader = data.get('uploader', 'Unknown Uploader')
        self.requester = requester

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, requester=None):
        loop = loop or asyncio.get_event_loop()
        cleaned_url = clean_youtube_url(url)
        data = None
        stream_url = None

        # Strategy 1: For YouTube links, fetch title via oEmbed and search via ytsearch1:
        if "youtube.com" in cleaned_url or "youtu.be" in cleaned_url:
            try:
                fetched_title = await fetch_video_title_oembed(cleaned_url)
                search_term = fetched_title if fetched_title else cleaned_url
                query = f"ytsearch1:{search_term}"
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
                stream_url, data = extract_stream_url(data)
            except Exception as e:
                print(f"[YTDL oEmbed Search Error] {e}")

        # Strategy 2: Direct extraction fallback if not YouTube link or if Strategy 1 failed
        if not stream_url:
            try:
                target_url = cleaned_url if (cleaned_url.startswith("ytsearch:") or "youtube.com" in cleaned_url or "youtu.be" in cleaned_url) else f"ytsearch:{cleaned_url}"
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(target_url, download=not stream))
                stream_url, data = extract_stream_url(data)
            except Exception as e:
                print(f"[YTDL Direct Extraction Error] {e}")

        # Strategy 3: Last-resort search
        if not stream_url:
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch1:{cleaned_url}", download=not stream))
                stream_url, data = extract_stream_url(data)
            except Exception:
                pass

        if not stream_url or not data:
            raise Exception("Could not extract video stream from YouTube.")

        return cls(discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS), data=data, requester=requester)

class MusicControlView(discord.ui.View):
    """Flavia-style Interactive Music Control Panel buttons."""

    def __init__(self, cog, ctx):
        super().__init__(timeout=None)
        self.cog = cog
        self.ctx = ctx

    @discord.ui.button(label="Pause / Play", style=discord.ButtonStyle.primary, emoji="⏯️")
    async def pause_play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Paused playback.", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Resumed playback.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ Nothing is playing to skip.", ephemeral=True)
        vc.stop()
        await interaction.response.send_message("⏭️ Skipped current track.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        self.cog.queues[guild_id] = []
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await interaction.response.send_message("🛑 Stopped playback and cleared queue.", ephemeral=True)

    @discord.ui.button(label="Loop", style=discord.ButtonStyle.success, emoji="🔁")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        self.cog.loop_status[guild_id] = not self.cog.loop_status.get(guild_id, False)
        status = "ENABLED 🔁" if self.cog.loop_status[guild_id] else "DISABLED ➡️"
        await interaction.response.send_message(f"Track looping is now **{status}**.", ephemeral=True)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📜")
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        queue = self.cog.get_queue(guild_id)
        if not queue:
            return await interaction.response.send_message("📜 Queue is currently empty.", ephemeral=True)
        
        description = "\n".join([f"**{i+1}.** [{item['title']}]({item['url']})" for i, item in enumerate(queue[:10])])
        if len(queue) > 10:
            description += f"\n\n*...and {len(queue)-10} more tracks.*"
            
        embed = discord.Embed(title="🎶 Current Music Queue", description=description, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Music(commands.Cog):
    """Flavia-style Music Cog with Interactive Buttons & Queue Management."""

    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.loop_status = {}
        self.current_track = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def format_duration(self, seconds):
        if not seconds:
            return "Live Stream 🔴"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)

        if self.loop_status.get(guild_id, False) and guild_id in self.current_track:
            track_info = self.current_track[guild_id]
        elif len(queue) > 0:
            track_info = queue.pop(0)
            self.current_track[guild_id] = track_info
        else:
            self.current_track.pop(guild_id, None)
            return await ctx.send("🎶 Queue is finished. Disconnecting or waiting for more tracks...")

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(track_info['url'], loop=self.bot.loop, stream=True, requester=track_info.get('requester'))
                
                def after_playing(error):
                    if error:
                        print(f"Music Playback Error: {error}")
                    asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

                ctx.voice_client.play(player, after=after_playing)

                embed = discord.Embed(
                    title="🎵 NOW PLAYING",
                    description=f"**[{player.title}]({player.url})**",
                    color=discord.Color.blue()
                )
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                embed.add_field(name="Uploader", value=player.uploader, inline=True)
                embed.add_field(name="Duration", value=self.format_duration(player.duration), inline=True)
                if player.requester:
                    embed.add_field(name="Requested By", value=player.requester.mention, inline=True)

                view = MusicControlView(self, ctx)
                await ctx.send(embed=embed, view=view)
            except Exception as e:
                await ctx.send(f"❌ Error loading track `{track_info.get('title')}`: {e}")
                await self.play_next(ctx)

    @commands.hybrid_command(name="join", description="Joins your current voice channel.")
    async def join(self, ctx: commands.Context):
        """Joins the user's voice channel."""
        if not ctx.author.voice:
            await ctx.send("❌ You are not connected to a voice channel.")
            return False
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"🔊 Moved to **{channel.name}**")
            return True
        await channel.connect()
        await ctx.send(f"🔊 Joined **{channel.name}**")
        return True

    @commands.hybrid_command(name="play", aliases=["p"], description="Plays music from YouTube or Spotify.")
    @app_commands.describe(search="Song name, YouTube URL, or Spotify playlist/track URL")
    async def play(self, ctx: commands.Context, *, search: str):
        """Plays music from YouTube or Spotify (Tracks, Playlists, Albums). Usage: /play <song or URL>"""
        if ctx.voice_client is None:
            connected = await self.join(ctx)
            if not connected:
                return

        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        search = clean_youtube_url(search.strip("<>"))

        # ── Spotify Link Support ───────────────────────────
        if "spotify.com" in search.lower():
            if ctx.interaction:
                await ctx.interaction.response.defer()
            msg = await ctx.send("🟢 Resolving Spotify link...")
            tracks = await fetch_spotify_tracks(search)
            if not tracks:
                return await msg.edit(content="❌ Could not extract tracks from Spotify link. (Please ensure playlist/track is public!)")
            
            added_count = 0
            for track_query in tracks:
                item = {"url": f"ytsearch:{track_query}", "title": track_query, "requester": ctx.author}
                queue.append(item)
                added_count += 1

            embed = discord.Embed(
                title="🟢 Spotify Music Enqueued",
                description=f"Added **{added_count} track(s)** from Spotify to queue!\nFirst track: **{tracks[0]}**",
                color=discord.Color.green()
            )
            await msg.edit(content="", embed=embed)

            if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                await self.play_next(ctx)
            return

        # ── YouTube / Regular Search ───────────────────────
        loop = self.bot.loop or asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False, process=False))
            title = info.get('title', search) if info else search
            url = info.get('webpage_url', search) if info else search
        except Exception:
            title = search
            url = search

        item = {"url": url, "title": title, "requester": ctx.author}
        queue.append(item)

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_next(ctx)
        else:
            embed = discord.Embed(
                title="📥 Added to Queue",
                description=f"**[{title}]({url})**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="leave", aliases=["dc", "disconnect"], description="Stops music and leaves the voice channel.")
    async def leave(self, ctx: commands.Context):
        """Stops music and disconnects the bot from the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from voice channel.")
        else:
            await ctx.send("❌ I am not in a voice channel.")

    @commands.hybrid_command(name="skip", aliases=["s"], description="Skips the currently playing track.")
    async def skip(self, ctx: commands.Context):
        """Skips the currently playing song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped current track.")
        else:
            await ctx.send("❌ Nothing is currently playing.")

    @commands.hybrid_command(name="stop", description="Stops playback and clears the queue.")
    async def stop(self, ctx: commands.Context):
        """Stops the music and clears the queue."""
        guild_id = ctx.guild.id
        self.queues[guild_id] = []
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.send("🛑 Stopped playback and cleared queue.")

    @commands.hybrid_command(name="queue", aliases=["q"], description="Displays the current music queue.")
    async def queue(self, ctx: commands.Context):
        """Displays the current music queue."""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        if not queue:
            return await ctx.send("📜 Queue is currently empty.")

        description = "\n".join([f"**{i+1}.** [{item['title']}]({item['url']})" for i, item in enumerate(queue[:10])])
        if len(queue) > 10:
            description += f"\n\n*...and {len(queue)-10} more tracks.*"

        embed = discord.Embed(title="🎶 Current Music Queue", description=description, color=discord.Color.purple())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
