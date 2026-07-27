import discord
from discord.ext import commands
import asyncio
import random
import yt_dlp

yt_dlp.utils.bug_reports_message = lambda: ''

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
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data, requester=requester)

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
            return await interaction.response.send_message("❌ I am not connected to a voice channel.", ephemeral=True)
        
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
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ Skipped current track.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing to skip.", ephemeral=True)

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

        # Check loop mode
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

                # Send Flavia-style Now Playing embed with interactive view buttons
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
                await ctx.send(f"❌ Error loading track: {e}")
                await self.play_next(ctx)

    @commands.command(name="join")
    async def join(self, ctx):
        """Joins the user's voice channel."""
        if not ctx.author.voice:
            await ctx.send("❌ You are not connected to a voice channel.")
            return False
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()
        await ctx.send(f"🔊 Joined **{channel.name}**")
        return True

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str):
        """Plays music from YouTube or adds it to the queue. Usage: !play <song name or URL>"""
        if ctx.voice_client is None:
            connected = await self.join(ctx)
            if not connected:
                return

        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        # Quick extract title for queue listing
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
            embed.set_footer(text=f"Queue Position: #{len(queue)}")
            await ctx.send(embed=embed)

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        """Skips currently playing song."""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped current track.")
        else:
            await ctx.send("❌ Nothing to skip.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops playback and clears queue."""
        self.queues[ctx.guild.id] = []
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("🛑 Playback stopped & queue cleared.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Shuffles the current queue."""
        queue = self.get_queue(ctx.guild.id)
        if len(queue) < 2:
            return await ctx.send("❌ Need at least 2 tracks in queue to shuffle.")
        random.shuffle(queue)
        await ctx.send("🔀 Shuffled music queue!")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        """Displays music queue."""
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("📜 Queue is empty.")
        
        description = "\n".join([f"**{i+1}.** [{item['title']}]({item['url']})" for i, item in enumerate(queue[:10])])
        if len(queue) > 10:
            description += f"\n\n*...and {len(queue)-10} more tracks.*"
            
        embed = discord.Embed(title="🎶 Current Music Queue", description=description, color=discord.Color.purple())
        await ctx.send(embed=embed)

    @commands.command(name="leave", aliases=["dc"])
    async def leave(self, ctx):
        """Leaves voice channel."""
        self.queues[ctx.guild.id] = []
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from voice channel.")

async def setup(bot):
    await bot.add_cog(Music(bot))
