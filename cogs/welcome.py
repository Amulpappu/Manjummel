import discord
from discord.ext import commands
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except Exception:
    HAS_PIL = False
import io
import aiohttp
import json
import os
import datetime

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

def hex_to_rgb(hex_str: str, default=(15, 23, 42)):
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 6:
        try:
            return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default

async def generate_welcome_card_image(member: discord.Member, config_data: dict, member_count: int) -> io.BytesIO:
    """Generates Koya-style Welcome Image Card with user avatar and dynamic text."""
    width, height = 1000, 500
    bg_rgb = hex_to_rgb(config_data.get("bg_color", "#0f172a"), (15, 23, 42))
    title_rgb = hex_to_rgb(config_data.get("title_color", "#00e678"), (0, 230, 120))
    name_rgb = hex_to_rgb(config_data.get("name_color", "#ff2d55"), (255, 45, 85))

    canvas = Image.new("RGBA", (width, height), (*bg_rgb, 255))
    draw = ImageDraw.Draw(canvas)

    # Cyan/emerald glowing outer border
    draw.rectangle([10, 10, width - 10, height - 10], outline=(0, 255, 170, 255), width=4)

    # Fetch avatar
    avatar_url = member.display_avatar.url
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                else:
                    avatar = Image.new("RGBA", (180, 180), (0, 255, 170, 255))
        except Exception:
            avatar = Image.new("RGBA", (180, 180), (0, 255, 170, 255))

    # Resize avatar to circular 180x180
    av_size = 180
    avatar = avatar.resize((av_size, av_size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (av_size, av_size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, av_size, av_size), fill=255)

    # Avatar ring glow
    ring_size = 200
    ring_x = (width - ring_size) // 2
    ring_y = 50
    draw.ellipse([ring_x, ring_y, ring_x + ring_size, ring_y + ring_size], outline=(0, 255, 170, 255), width=6)

    # Paste circular avatar
    av_x = (width - av_size) // 2
    av_y = 60
    canvas.paste(avatar, (av_x, av_y), mask)

    # Fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 52)
        font_name = ImageFont.truetype("arial.ttf", 36)
        font_sub = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_large = font_name = font_sub = ImageFont.load_default()

    # Draw WELCOME title
    title_text = config_data.get("welcome_title", "WELCOME").upper()
    draw.text((width // 2, 280), title_text, fill=(*title_rgb, 255), font=font_large, anchor="mm")

    # Draw USERNAME#DISCRIMINATOR
    display_name = f"{member.name.upper()}#{member.discriminator}" if member.discriminator != "0" else member.display_name.upper()
    draw.text((width // 2, 350), display_name, fill=(*name_rgb, 255), font=font_name, anchor="mm")

    # Draw Subtitle (e.g. HI GUYS)
    subtext = config_data.get("welcome_subtitle", "HI GUYS").upper()
    draw.text((width // 2, 410), subtext, fill=(255, 255, 255, 255), font=font_sub, anchor="mm")

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output

UNICODE_MAP = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h',
    'ɪ': 'i', 'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p',
    'ǫ': 'q', 'ʀ': 'r', 'ꜱ': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x',
    'ʏ': 'y', 'ᴢ': 'z', '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5',
    '6': '6', '7': '7', '8': '8', '9': '9'
}

def normalize_unicode_text(text: str) -> str:
    res = []
    for char in text.lower():
        if char in UNICODE_MAP:
            res.append(UNICODE_MAP[char])
        else:
            res.append(char)
    return "".join(res)

class Welcome(commands.Cog):
    """Koya-Style Welcome Cards & Custom Web Dashboard Manager for Manjummel Bot."""

    def __init__(self, bot):
        self.bot = bot
        self.config_data = load_welcome_config()

    def get_welcome_channel(self, guild: discord.Guild):
        """Finds channel matching welcome_config channel name or #🙏┆ᴡᴇʟᴄᴏᴍᴇ, prioritizing exact welcome channel over #welcome-and-rules."""
        cfg = load_welcome_config()
        target_raw = cfg.get("channel_name", "welcome").strip()
        target_norm = normalize_unicode_text(target_raw)

        def clean_ch_name(name: str) -> str:
            norm = normalize_unicode_text(name)
            for prefix in ["🙏┆", "⚡┆", "┆", "🙏", "⚡"]:
                norm = norm.replace(prefix, "")
            return norm.strip("-_ ")

        # Pass 1: Exact raw name match (e.g. "🙏┆ᴡᴇʟᴄᴏᴍᴇ")
        for channel in guild.text_channels:
            if channel.name == target_raw or channel.name.lower() == target_raw.lower():
                return channel

        # Pass 2: Clean normalized exact match == "welcome" (matches #🙏┆ᴡᴇʟᴄᴏᴍᴇ, #welcome)
        for channel in guild.text_channels:
            cleaned = clean_ch_name(channel.name)
            if cleaned == "welcome" or cleaned == "welcom":
                return channel

        # Pass 3: Channel containing "welcome" BUT excluding compound rules/logs channels (e.g. exclude #welcome-and-rules)
        for channel in guild.text_channels:
            ch_norm = normalize_unicode_text(channel.name)
            if "welcome" in ch_norm or "welcom" in ch_norm:
                if not any(ex in ch_norm for ex in ["rule", "rules", "log", "logs", "info", "notice"]):
                    return channel

        # Pass 4: Fallback to system_channel or first text channel
        if guild.system_channel:
            return guild.system_channel
        if guild.text_channels:
            return guild.text_channels[0]
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.config_data.get("enabled", True):
            return

        guild = member.guild
        channel = self.get_welcome_channel(guild)

        # Auto-assign role (e.g. @family)
        role_name = self.config_data.get("auto_role", "family")
        auto_role = discord.utils.get(guild.roles, name=role_name)
        if not auto_role:
            for r in guild.roles:
                if role_name.lower() in r.name.lower():
                    auto_role = r
                    break
        if auto_role:
            try:
                await member.add_roles(auto_role, reason="Auto-assigned role on join")
            except Exception as e:
                print(f"[Welcome Auto-Role Error] {e}")

        if channel:
            await self.send_welcome_message(channel, member)

    async def send_welcome_message(self, channel: discord.TextChannel, member: discord.Member):
        """Sends exact Koya-formatted text message and generated image card."""
        cfg = load_welcome_config()
        server_name = cfg.get("server_name", channel.guild.name)
        line2 = cfg.get("line2", "Have A Great Time here ❤️")
        rules_channel = cfg.get("rules_channel", "#📖┆DISCORD-RULES")
        member_count = channel.guild.member_count

        msg_content = (
            f"{member.mention}\n"
            f"======= (🎉) =======\n"
            f"🌹 Welcome To {server_name} ▫️\n"
            f"🌹 {line2}\n"
            f"🌹 You Are the {member_count} Member On {server_name} ▫️\n"
            f"🌹 Follow our Discord Rules {rules_channel} ▫️\n"
            f"======= (🔥) ======="
        )

        if HAS_PIL:
            try:
                image_buf = await generate_welcome_card_image(member, cfg, member_count)
                file = discord.File(fp=image_buf, filename="welcome_card.png")
                await channel.send(content=msg_content, file=file)
                return
            except Exception as e:
                print(f"[Welcome Image Error] {e}")

        await channel.send(content=msg_content)

    @commands.command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx, member: discord.Member = None):
        """Sends test Koya-style welcome card message to the welcome channel."""
        target = member or ctx.author
        channel = self.get_welcome_channel(ctx.guild)
        if channel:
            await self.send_welcome_message(channel, target)
            await ctx.send(f"✅ Sent test Koya welcome card for {target.mention} to {channel.mention}!")
        else:
            await ctx.send("❌ Could not find welcome channel.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
