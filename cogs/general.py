import discord
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

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Checks the bot's response time."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

    @commands.command(name="botinfo")
    async def botinfo(self, ctx):
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

    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, *, role_name: str):
        """Assigns a role to a member. Usage: !addrole @user RoleName"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Successfully assigned role **{role.name}** to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to assign that role.")

    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, *, role_name: str):
        """Removes a role from a member. Usage: !removerole @user RoleName"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found in this server.")
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Successfully removed role **{role.name}** from {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to remove that role.")

async def setup(bot):
    await bot.add_cog(General(bot))
