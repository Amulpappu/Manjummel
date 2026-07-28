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

    @commands.hybrid_command(name="flames", description="Calculates the FLAMES relationship status between two users.")
    @app_commands.describe(user1="First user", user2="Second user")
    async def flames(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """Calculates FLAMES relationship test between two users."""
        name1 = list(user1.display_name.lower().replace(" ", ""))
        name2 = list(user2.display_name.lower().replace(" ", ""))

        # Cancel out common characters
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

    @commands.hybrid_command(name="love", description="Calculates the love compatibility percentage between two users.")
    @app_commands.describe(user1="First partner", user2="Second partner or user")
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User = None):
        """Calculates love compatibility percentage between two users."""
        partner1 = user1
        partner2 = user2 or ctx.author

        if partner1.id == partner2.id:
            score = 100
        else:
            sorted_ids = sorted([partner1.id, partner2.id])
            score = (sorted_ids[0] * 7 + sorted_ids[1] * 13 + 77) % 101

        filled_blocks = int(score / 10)
        bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

        if score >= 90:
            message = "💖 **Perfect Match!** True soulmates destined for eternity!"
            color = discord.Color.red()
        elif score >= 75:
            message = "💕 **High Compatibility!** Love is in the air, sparks flying!"
            color = discord.Color.magenta()
        elif score >= 50:
            message = "🥰 **Good Match!** Great potential for a sweet relationship!"
            color = discord.Color.gold()
        elif score >= 30:
            message = "⚡ **Sparks Flying!** Needs a little effort, but has potential!"
            color = discord.Color.orange()
        else:
            message = "💔 **Low Compatibility...** Best to stay great best friends!"
            color = discord.Color.dark_grey()

        embed = discord.Embed(
            title="💘 Love Compatibility Calculator",
            description=f"**{partner1.display_name}** ❤️ **{partner2.display_name}**\n\n"
                        f"**Love Score:** `{score}%`\n"
                        f"`[{bar}]`\n\n"
                        f"{message}",
            color=color
        )
        embed.set_thumbnail(url=partner1.display_avatar.url)
        embed.set_footer(text=f"Calculated by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
