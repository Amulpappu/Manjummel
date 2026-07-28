import discord
from discord import app_commands
from discord.ext import commands
import time
import config

class General(commands.Cog):
    """Koya-style Welcome Cards, General Utility, and Role Management."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Sends a Koya-style rich Welcome Card when a new user joins."""
        ch_id = config.WELCOME_CHANNEL_ID or config.ANNOUNCEMENT_CHANNEL_ID
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                member_count = member.guild.member_count
                embed = discord.Embed(
                    title=f"🌸 Welcome to {member.guild.name}!",
                    description=f"Welcome {member.mention}! We're delighted to have you here.\n\n"
                                f"🏷️ **Member Count:** You are member **#{member_count}**!\n"
                                f"📅 **Account Age:** <t:{int(member.created_at.timestamp())}:R>\n\n"
                                f"Please review the server rules and enjoy your stay! ✨",
                    color=discord.Color.purple()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"User ID: {member.id} • {member.guild.name}", icon_url=member.guild.icon.url if member.guild.icon else None)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Sends a leave message when a user leaves the server."""
        ch_id = config.WELCOME_CHANNEL_ID or config.ANNOUNCEMENT_CHANNEL_ID
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Goodbye!",
                    description=f"**{member.display_name}** has left the server.\nWe now have `{member.guild.member_count}` members.",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

    @commands.hybrid_command(name="ping", description="Checks the bot's response time.")
    async def ping(self, ctx: commands.Context):
        """Checks the bot's response time."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

    @commands.hybrid_command(name="botinfo", description="Displays information about Manjummel Bot.")
    async def botinfo(self, ctx: commands.Context):
        """Displays information about Manjummel Bot."""
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = discord.Embed(
            title="🤖 Manjummel Bot — Ultimate All-In-One",
            description="Your feature-rich Discord bot featuring Music (Flavia), Welcome Cards (Koya), Invite Tracker, Moderation (ProBot/Carl), and Birthday Celebrations (WishWave)!",
            color=discord.Color.blue()
        )

        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="addrole", description="Assigns a role to a member.")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to give the role to", role_name="The exact name of the role")
    async def add_role(self, ctx: commands.Context, member: discord.Member, role_name: str):
        """Assigns a role to a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Successfully assigned role **{role.name}** to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to assign that role.")

    @commands.hybrid_command(name="removerole", description="Removes a role from a member.")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role_name="The exact name of the role")
    async def remove_role(self, ctx: commands.Context, member: discord.Member, role_name: str):
        """Removes a role from a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Successfully removed role **{role.name}** from {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to remove that role.")

    @commands.hybrid_command(name="avatar", aliases=["av"], description="Displays a user's avatar image.")
    @app_commands.describe(user="Optional user to view avatar for")
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """Displays the avatar of a specified user or yourself."""
        target = user or ctx.author
        avatar_url = target.display_avatar.url

        embed = discord.Embed(
            title=f"🖼️ Avatar for {target.display_name}",
            color=target.accent_color or discord.Color.purple()
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🔗 Open High-Res Avatar", url=avatar_url, style=discord.ButtonStyle.link))

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="banner", description="Displays a user's profile banner image.")
    @app_commands.describe(user="Optional user to view banner for")
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        """Displays the profile banner of a specified user or yourself."""
        target = user or ctx.author

        try:
            full_user = await self.bot.fetch_user(target.id)
        except Exception:
            full_user = target

        if full_user.banner:
            banner_url = full_user.banner.url
            embed = discord.Embed(
                title=f"🚩 Profile Banner for {full_user.display_name}",
                color=full_user.accent_color or discord.Color.purple()
            )
            embed.set_image(url=banner_url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="🔗 Open High-Res Banner", url=banner_url, style=discord.ButtonStyle.link))

            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title=f"🚩 Profile Banner for {full_user.display_name}",
                description=f"**{full_user.display_name}** does not have a custom profile banner set.",
                color=full_user.accent_color or discord.Color.dark_gray()
            )
            if full_user.accent_color:
                embed.add_field(name="Accent Color", value=f"`{full_user.accent_color}`", inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")

import aiohttp
import io
import math
from PIL import Image, ImageDraw, ImageFont

def get_card_font(size: int):
    FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")
    if os.path.exists(FONT_PATH):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_heart_contour(draw, center, size, color):
    cx, cy = center
    points = []
    for t in [i * 0.02 for i in range(314)]:
        x = 16 * (math.sin(t) ** 3)
        y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        points.append((cx + x * (size / 16), cy + y * (size / 16)))
    draw.polygon(points, outline=color, width=6)

async def fetch_avatar_bytes(user: discord.User) -> bytes:
    try:
        url = user.display_avatar.with_format("png").url
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"[Avatar Fetch Error] {e}")
    return b""

def generate_compatibility_card(user1_bytes: bytes, user2_bytes: bytes, score: int, mode: str = "love") -> io.BytesIO:
    width, height = 900, 320

    if mode == "hate":
        bg_fill = (45, 20, 25, 255)
        card_fill = (65, 25, 35, 230)
        outline_color = (255, 75, 75, 200)
    elif mode == "friendship":
        bg_fill = (15, 35, 45, 255)
        card_fill = (25, 55, 75, 230)
        outline_color = (75, 200, 255, 200)
    else:
        bg_fill = (25, 15, 40, 255)
        card_fill = (55, 30, 80, 230)
        outline_color = (220, 140, 255, 200)

    bg = Image.new("RGBA", (width, height), bg_fill)
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    
    margin = 20
    card_draw.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=25,
        fill=card_fill,
        outline=outline_color,
        width=3
    )

    bg = Image.alpha_composite(bg, card)
    draw = ImageDraw.Draw(bg)

    av_size = 180
    
    def process_avatar(raw_bytes):
        if raw_bytes:
            try:
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                img = img.resize((av_size, av_size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (av_size, av_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
                output = Image.new("RGBA", (av_size, av_size), (0, 0, 0, 0))
                output.paste(img, (0, 0), mask)
                return output
            except Exception:
                pass
        
        fb = Image.new("RGBA", (av_size, av_size), (120, 100, 160, 255))
        mask = Image.new("L", (av_size, av_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
        fb.putalpha(mask)
        return fb

    av1 = process_avatar(user1_bytes)
    av2 = process_avatar(user2_bytes)

    # Ring 1
    r1_x, r1_y = 80, (height - av_size) // 2
    draw.ellipse([r1_x - 5, r1_y - 5, r1_x + av_size + 5, r1_y + av_size + 5], outline=(255, 255, 255, 240), width=5)
    bg.paste(av1, (r1_x, r1_y), av1)

    # Ring 2
    r2_x, r2_y = width - 80 - av_size, (height - av_size) // 2
    draw.ellipse([r2_x - 5, r2_y - 5, r2_x + av_size + 5, r2_y + av_size + 5], outline=(255, 255, 255, 240), width=5)
    bg.paste(av2, (r2_x, r2_y), av2)

    # Center Heart & Text
    cx, cy = width // 2, height // 2
    draw_heart_contour(draw, (cx, cy - 10), 9.5, (255, 255, 255, 240))

    font_score = get_card_font(52)
    draw.text((cx, cy - 10), f"{score}%", fill=(255, 255, 255, 255), font=font_score, anchor="mm")

    output = io.BytesIO()
    bg.save(output, format="PNG")
    output.seek(0)
    return output

class LoveControlView(discord.ui.View):
    def __init__(self, cog, user1: discord.User, user2: discord.User, current_mode: str = "love"):
        super().__init__(timeout=180)
        self.cog = cog
        self.user1 = user1
        self.user2 = user2
        self.current_mode = current_mode

    @discord.ui.button(label="Random", style=discord.ButtonStyle.secondary, emoji="🎲")
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        members = [m for m in interaction.guild.members if not m.bot and m.id != self.user1.id]
        if not members:
            members = [m for m in interaction.guild.members if not m.bot]
        import random
        random_user = random.choice(members)
        self.user2 = random_user
        await self.cog.dispatch_love_response(interaction, self.user1, self.user2, mode=self.current_mode, edit=True)

    @discord.ui.button(label="Hate", style=discord.ButtonStyle.danger, emoji="💔")
    async def hate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_mode = "hate"
        await self.cog.dispatch_love_response(interaction, self.user1, self.user2, mode="hate", edit=True)

    @discord.ui.button(label="Friendship", style=discord.ButtonStyle.primary, emoji="⭐")
    async def friendship_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_mode = "friendship"
        await self.cog.dispatch_love_response(interaction, self.user1, self.user2, mode="friendship", edit=True)

class General(commands.Cog):
    """Koya-style Welcome Cards, General Utility, and Role Management."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    async def dispatch_love_response(self, target_ctx_or_interaction, user1: discord.User, user2: discord.User, mode: str = "love", edit: bool = False):
        if user1.id == user2.id:
            score = 100
        else:
            sorted_ids = sorted([user1.id, user2.id])
            if mode == "hate":
                score = (sorted_ids[0] * 3 + sorted_ids[1] * 19 + 42) % 101
            elif mode == "friendship":
                score = (sorted_ids[0] * 11 + sorted_ids[1] * 5 + 88) % 101
            else:
                score = (sorted_ids[0] * 7 + sorted_ids[1] * 13 + 77) % 101

        if mode == "hate":
            quotes = [
                f"In this endless universe, **{user1.display_name}** and **{user2.display_name}** are total arch-enemies! ⚔️",
                f"Sparks of fury! **{user1.display_name}** and **{user2.display_name}** cannot stand each other! 💥"
            ]
            title_text = "Hate"
            emoji_icon = "💔"
        elif mode == "friendship":
            quotes = [
                f"Best buddies for life! **{user1.display_name}** and **{user2.display_name}** share an unbreakable bond ⭐",
                f"Pure friendship energy! **{user1.display_name}** and **{user2.display_name}** always have each other's back 🤜🤛"
            ]
            title_text = "Friendship"
            emoji_icon = "⭐"
        else:
            if score >= 90:
                quote = f"**{user1.display_name}** and **{user2.display_name}** are crazy about each other... pure chaotic love 🔥"
            elif score >= 50:
                quote = f"Wherever **{user1.display_name}** and **{user2.display_name}** go, romance follows! 💕"
            else:
                quote = f"In this endless universe, **{user1.display_name}** and **{user2.display_name}** are just two distant stars 🪐"
            quotes = [quote]
            title_text = "Love"
            emoji_icon = "💖"

        import random
        quote_msg = random.choice(quotes)
        header_text = f"{user1.mention} + {user2.mention} = **{score}%** of {title_text} {emoji_icon}\n{quote_msg}"

        b1 = await fetch_avatar_bytes(user1)
        b2 = await fetch_avatar_bytes(user2)
        card_buf = generate_compatibility_card(b1, b2, score, mode=mode)
        file = discord.File(fp=card_buf, filename="love_card.png")
        view = LoveControlView(self, user1, user2, current_mode=mode)

        if isinstance(target_ctx_or_interaction, discord.Interaction):
            if edit:
                await target_ctx_or_interaction.followup.send(content=header_text, file=file, view=view)
            else:
                await target_ctx_or_interaction.response.send_message(content=header_text, file=file, view=view)
        else:
            await target_ctx_or_interaction.send(content=header_text, file=file, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Sends a Koya-style rich Welcome Card when a new user joins."""
        ch_id = config.WELCOME_CHANNEL_ID or config.ANNOUNCEMENT_CHANNEL_ID
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                member_count = member.guild.member_count
                embed = discord.Embed(
                    title=f"🌸 Welcome to {member.guild.name}!",
                    description=f"Welcome {member.mention}! We're delighted to have you here.\n\n"
                                f"🏷️ **Member Count:** You are member **#{member_count}**!\n"
                                f"📅 **Account Age:** <t:{int(member.created_at.timestamp())}:R>\n\n"
                                f"Please review the server rules and enjoy your stay! ✨",
                    color=discord.Color.purple()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"User ID: {member.id} • {member.guild.name}", icon_url=member.guild.icon.url if member.guild.icon else None)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Sends a leave message when a user leaves the server."""
        ch_id = config.WELCOME_CHANNEL_ID or config.ANNOUNCEMENT_CHANNEL_ID
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                embed = discord.Embed(
                    title="👋 Goodbye!",
                    description=f"**{member.display_name}** has left the server.\nWe now have `{member.guild.member_count}` members.",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

    @commands.hybrid_command(name="ping", description="Checks the bot's response time.")
    async def ping(self, ctx: commands.Context):
        """Checks the bot's response time."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

    @commands.hybrid_command(name="botinfo", description="Displays information about Manjummel Bot.")
    async def botinfo(self, ctx: commands.Context):
        """Displays information about Manjummel Bot."""
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = discord.Embed(
            title="🤖 Manjummel Bot — Ultimate All-In-One",
            description="Your feature-rich Discord bot featuring Music (Flavia), Welcome Cards (Koya), Invite Tracker, Moderation (ProBot/Carl), and Birthday Celebrations (WishWave)!",
            color=discord.Color.blue()
        )

        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="addrole", description="Assigns a role to a member.")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to give the role to", role_name="The exact name of the role")
    async def add_role(self, ctx: commands.Context, member: discord.Member, role_name: str):
        """Assigns a role to a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Successfully assigned role **{role.name}** to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to assign that role.")

    @commands.hybrid_command(name="removerole", description="Removes a role from a member.")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to remove the role from", role_name="The exact name of the role")
    async def remove_role(self, ctx: commands.Context, member: discord.Member, role_name: str):
        """Removes a role from a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Successfully removed role **{role.name}** from {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to remove that role.")

    @commands.hybrid_command(name="avatar", aliases=["av"], description="Displays a user's avatar image.")
    @app_commands.describe(user="Optional user to view avatar for")
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """Displays the avatar of a specified user or yourself."""
        target = user or ctx.author
        avatar_url = target.display_avatar.url

        embed = discord.Embed(
            title=f"🖼️ Avatar for {target.display_name}",
            color=target.accent_color or discord.Color.purple()
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🔗 Open High-Res Avatar", url=avatar_url, style=discord.ButtonStyle.link))

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="banner", description="Displays a user's profile banner image.")
    @app_commands.describe(user="Optional user to view banner for")
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        """Displays the profile banner of a specified user or yourself."""
        target = user or ctx.author

        try:
            full_user = await self.bot.fetch_user(target.id)
        except Exception:
            full_user = target

        if full_user.banner:
            banner_url = full_user.banner.url
            embed = discord.Embed(
                title=f"🚩 Profile Banner for {full_user.display_name}",
                color=full_user.accent_color or discord.Color.purple()
            )
            embed.set_image(url=banner_url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="🔗 Open High-Res Banner", url=banner_url, style=discord.ButtonStyle.link))

            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title=f"🚩 Profile Banner for {full_user.display_name}",
                description=f"**{full_user.display_name}** does not have a custom profile banner set.",
                color=full_user.accent_color or discord.Color.dark_gray()
            )
            if full_user.accent_color:
                embed.add_field(name="Accent Color", value=f"`{full_user.accent_color}`", inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="flames", description="Calculates the FLAMES relationship status between two users.")
    @app_commands.describe(user1="First user", user2="Second user")
    async def flames(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Calculates FLAMES relationship test between two users."""
        name1 = list(user1.display_name.lower().replace(" ", ""))
        name2 = list(user2.display_name.lower().replace(" ", ""))

        for char in name1[:]:
            if char in name2:
                name1.remove(char)
                name2.remove(char)

        total_count = len(name1) + len(name2)

        flames_dict = {
            "F": ("Friends 🤝", "Best friends forever! A bond built on trust and fun."),
            "L": ("Lovers 💕", "Passionate lovers! Sparks are flying everywhere!"),
            "A": ("Affection 🥰", "Sweet affection! Deep emotional care and warm feelings."),
            "M": ("Marriage 💍", "Wedding bells ringing! Destined for lifelong marriage!"),
            "E": ("Enemies ⚔️", "Fierce rivals! Watch out for arguments and friendly battles."),
            "S": ("Siblings 👫", "Brother/Sister bond! Protective, caring, and inseparable.")
        }
        flames_list = ["F", "L", "A", "M", "E", "S"]

        if total_count > 0:
            index = 0
            while len(flames_list) > 1:
                index = (index + total_count - 1) % len(flames_list)
                flames_list.pop(index)
            result_code = flames_list[0]
        else:
            result_code = "L"

        status, desc = flames_dict[result_code]

        embed = discord.Embed(
            title="🔥 FLAMES Relationship Calculator",
            description=f"Testing compatibility between **{user1.display_name}** & **{user2.display_name}**...\n\n"
                        f"✨ **FLAMES Result:** `{status}`\n"
                        f"📝 {desc}",
            color=discord.Color.magenta()
        )
        embed.set_thumbnail(url=user1.display_avatar.url)
        embed.set_footer(text=f"FLAMES Count: {total_count} • Tested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="love", description="Calculates the love compatibility percentage between two users with a graphic card.")
    @app_commands.describe(user1="First partner", user2="Second partner or user")
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User = None):
        """Calculates love compatibility percentage between two users."""
        partner1 = user1
        partner2 = user2 or ctx.author
        await self.dispatch_love_response(ctx, partner1, partner2, mode="love")

async def setup(bot):
    await bot.add_cog(General(bot))
