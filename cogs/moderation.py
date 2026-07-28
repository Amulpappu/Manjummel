import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import datetime
import config

class Moderation(commands.Cog):
    """ProBot, Carl-bot & StatBot style Moderation, Audit Logging & Server Analytics."""

    def __init__(self, bot):
        self.bot = bot
        self.warns_file = os.path.join(config.DATA_DIR, "warnings.json")
        self.warnings = self.load_warnings()

    def load_warnings(self):
        if os.path.exists(self.warns_file):
            try:
                with open(self.warns_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_warnings(self):
        with open(self.warns_file, "w", encoding="utf-8") as f:
            json.dump(self.warnings, f, indent=4)

    # ── Audit Log Listeners (Carl-bot / ProBot style) ──────────
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Logs deleted messages."""
        if message.author.bot or not message.guild:
            return
        ch_id = config.ANNOUNCEMENT_CHANNEL_ID or config.WELCOME_CHANNEL_ID
        channel = message.guild.get_channel(ch_id)
        if channel and channel.id != message.channel.id:
            embed = discord.Embed(
                title="🗑️ Message Deleted",
                description=f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                            f"**Channel:** {message.channel.mention}\n\n"
                            f"**Content:**\n{message.content or '*No text content (embed or attachment)*'}",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"User ID: {message.author.id}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Logs edited messages."""
        if before.author.bot or before.content == after.content or not before.guild:
            return
        ch_id = config.ANNOUNCEMENT_CHANNEL_ID or config.WELCOME_CHANNEL_ID
        channel = before.guild.get_channel(ch_id)
        if channel and channel.id != before.channel.id:
            embed = discord.Embed(
                title="✏️ Message Edited",
                description=f"**Author:** {before.author.mention} (`{before.author.id}`)\n"
                            f"**Channel:** {before.channel.mention}\n"
                            f"[Jump to Message]({after.jump_url})\n\n"
                            f"**Before:**\n{before.content}\n\n"
                            f"**After:**\n{after.content}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # ── Moderation Commands ───────────────────────────────────
    @commands.hybrid_command(name="warn", description="Warns a member in the server.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def warn_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Warns a member. Usage: /warn @user Spamming chat"""
        user_id_str = str(member.id)
        if user_id_str not in self.warnings:
            self.warnings[user_id_str] = []

        warn_entry = {
            "moderator": ctx.author.display_name,
            "reason": reason,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.warnings[user_id_str].append(warn_entry)
        self.save_warnings()

        count = len(self.warnings[user_id_str])
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned by {ctx.author.mention}.\n"
                        f"**Reason:** {reason}\n"
                        f"**Total Warnings:** `{count}`",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="warns", description="Displays warning history for a user.")
    @app_commands.describe(member="Optional member to check warnings for")
    async def get_warns(self, ctx: commands.Context, member: discord.Member = None):
        """Displays warning history for a user."""
        target = member or ctx.author
        user_id_str = str(target.id)
        user_warns = self.warnings.get(user_id_str, [])

        if not user_warns:
            return await ctx.send(f"✅ {target.display_name} has clean records (0 warnings).")

        embed = discord.Embed(
            title=f"⚠️ Warning History for {target.display_name}",
            color=discord.Color.gold()
        )
        for idx, w in enumerate(user_warns, 1):
            embed.add_field(
                name=f"Warning #{idx} — {w['date']}",
                value=f"**Mod:** {w['moderator']}\n**Reason:** {w['reason']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", description="Clears all warnings for a user.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to clear warnings for")
    async def clear_warns(self, ctx: commands.Context, member: discord.Member):
        """Clears all warnings for a user."""
        user_id_str = str(member.id)
        if user_id_str in self.warnings:
            del self.warnings[user_id_str]
            self.save_warnings()
        await ctx.send(f"🧹 Cleared all warnings for {member.mention}.")

    @commands.hybrid_command(name="kick", description="Kicks a member from the server.")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    async def kick_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kicks a member from the server."""
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked **{member.display_name}** | Reason: {reason}")

    @commands.hybrid_command(name="ban", description="Bans a member from the server.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="Reason for banning")
    async def ban_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Bans a member from the server."""
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned **{member.display_name}** | Reason: {reason}")

    @commands.hybrid_command(name="purge", aliases=["clear"], description="Deletes multiple messages in channel.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def purge_messages(self, ctx: commands.Context, amount: int = 10):
        """Deletes multiple messages in channel."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.interaction.followup.send(f"🧹 Deleted `{len(deleted)}` messages.", ephemeral=True)
        else:
            deleted = await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"🧹 Deleted `{len(deleted)-1}` messages.")
            await msg.delete(delay=3)

    # ── StatBot Analytics Commands ───────────────────────────
    @commands.hybrid_command(name="serverinfo", aliases=["sinfo"], description="Displays rich server statistics.")
    async def server_info(self, ctx: commands.Context):
        """Displays rich StatBot-style server statistics."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"📊 Server Information — {guild.name}",
            color=discord.Color.blue()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=f"{guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)

        embed.add_field(name="Total Members", value=f"👥 `{guild.member_count}`", inline=True)
        embed.add_field(name="Roles Count", value=f"🎭 `{len(guild.roles)}`", inline=True)
        embed.add_field(name="Channels", value=f"💬 `{len(guild.text_channels)}` Text | 🔊 `{len(guild.voice_channels)}` Voice", inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", aliases=["uinfo"], description="Displays detailed user profile information.")
    @app_commands.describe(member="Optional member to view info for")
    async def user_info(self, ctx: commands.Context, member: discord.Member = None):
        """Displays detailed user profile information."""
        target = member or ctx.author
        roles = [role.mention for role in target.roles if role.name != "@everyone"]

        embed = discord.Embed(
            title=f"👤 User Profile — {target.display_name}",
            color=target.color
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="User ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Account Created", value=target.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Joined Server", value=target.joined_at.strftime("%Y-%m-%d") if target.joined_at else "Unknown", inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:10]) if roles else "None", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
