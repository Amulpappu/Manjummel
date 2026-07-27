import discord
from discord.ext import commands
import datetime
import config

def format_time_ago(dt: datetime.datetime) -> str:
    """Format datetime into human-readable time ago (e.g. 4 years ago, 9 days ago)."""
    now = datetime.datetime.utcnow()
    diff = now - dt
    days = diff.days
    years = days // 365
    months = days // 30
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if years >= 1:
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif months >= 1:
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif days >= 1:
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif minutes >= 1:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

class ServerLogging(commands.Cog):
    """Comprehensive Discord Audit & Event Logging Cog matching Yazhini & Manjummel styling."""

    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild: discord.Guild, target_names: list[str]):
        """Helper to find a log channel by name (fuzzy match across formatted names)."""
        for channel in guild.text_channels:
            name_clean = channel.name.lower().replace("⚡┆", "").replace("📋┆", "").replace("🎭┆", "").replace("⚙️┆", "").replace("🛡️┆", "").replace("-", "_")
            for target in target_names:
                t_clean = target.lower().replace("-", "_")
                if t_clean in name_clean or name_clean in t_clean:
                    return channel
        return None

    def add_footer(self, embed: discord.Embed, author=None):
        """Standardized footer matching Manjummel™ style."""
        now_str = datetime.datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")
        prefix = f"{author.name} • " if author else "Manjummel™ • "
        embed.set_footer(text=f"{prefix}{now_str}")

    # ── Automatic Channel Creation Command ───────────────────
    @commands.command(name="setupchannels", aliases=["createlogchannels"])
    @commands.has_permissions(administrator=True)
    async def setup_log_channels(self, ctx):
        """Automatically creates formatted announcement & audit log channels under category."""
        guild = ctx.guild
        category_name = "----DISCORD LOGS----"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            await ctx.send(f"📁 Created category **{category_name}**.")

        channels_to_create = [
            ("⚡┆JOIN-LOGS", "Audit logs for member joins and account age."),
            ("⚡┆LEAVE-LOGS", "Audit logs for member leaves and kicks."),
            ("⚡┆ROLE-LOGS", "Audit logs for role assignments and permission updates."),
            ("⚡┆SERVER-LOGS", "Audit logs for channel creations, role edits, and message deletions."),
            ("⚡┆MODERATOR-ONLY", "Audit logs for voice channel activity and moderator actions."),
            ("⚡┆INVITE-LOGS", "Audit logs for server invite tracking."),
            ("🎂┆ʙɪʀᴛʜᴅᴀʏ-ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ", "Channel for birthday celebration cards."),
            ("🙏┆ᴡᴇʟᴄᴏᴍᴇ", "Channel for welcoming new members."),
        ]

        created_count = 0
        for name, topic in channels_to_create:
            existing = discord.utils.get(guild.text_channels, name=name)
            if not existing:
                await guild.create_text_channel(name, category=category, topic=topic)
                created_count += 1

        await ctx.send(f"✅ Setup complete! Created `{created_count}` logging channels under **{category_name}**.")

    # ── 1. Join & Leave Logs (⚡┆JOIN-LOGS & ⚡┆LEAVE-LOGS) ───
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.get_log_channel(member.guild, ["join_logs", "join_leave_logs"])
        if channel:
            created_at = member.created_at
            date_str = created_at.strftime("%d/%m/%Y %H:%M")
            time_ago = format_time_ago(created_at)

            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"{member.mention} **joined the server.**\n\n"
                            f"⏱ **Age of account:**\n"
                            f"`{date_str}`\n"
                            f"**{time_ago}**",
                color=discord.Color.from_rgb(0, 168, 107)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            self.add_footer(embed)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.get_log_channel(member.guild, ["leave_logs", "join_leave_logs"])
        if channel:
            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"📤 {member.mention} **left the server.**\n\n"
                            f"**IDs**\n"
                            f"`{member.mention}` (`{member.id}`)",
                color=discord.Color.from_rgb(220, 53, 69)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            self.add_footer(embed)
            await channel.send(embed=embed)

    # ── 2. Role & Nickname Logs (⚡┆ROLE-LOGS & ⚡┆MODERATOR-ONLY) ─
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Role Changes (⚡┆ROLE-LOGS)
        if before.roles != after.roles:
            role_channel = self.get_log_channel(before.guild, ["role_logs"])
            if role_channel:
                added_roles = [r.mention for r in after.roles if r not in before.roles]
                removed_roles = [r.mention for r in before.roles if r not in after.roles]

                if added_roles:
                    embed = discord.Embed(
                        title="🎭 Role Assigned",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Added Role(s):** {', '.join(added_roles)}",
                        color=discord.Color.blue()
                    )
                    self.add_footer(embed)
                    await role_channel.send(embed=embed)

                if removed_roles:
                    embed = discord.Embed(
                        title="🎭 Role Removed",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Removed Role(s):** {', '.join(removed_roles)}",
                        color=discord.Color.orange()
                    )
                    self.add_footer(embed)
                    await role_channel.send(embed=embed)

        # Server Nickname Changes (⚡┆MODERATOR-ONLY)
        if before.nick != after.nick:
            mod_channel = self.get_log_channel(before.guild, ["moderator_only", "moderator_logs", "mod_logs"])
            if mod_channel:
                old_nick = before.nick if before.nick else "None (No Nickname)"
                new_nick = after.nick if after.nick else "None (Reset to Username)"
                embed = discord.Embed(
                    title="✏️ Server Nickname Changed",
                    description=f"**User:** {after.mention} (`{after.id}`)\n"
                                f"**Discord Username:** `{after.name}`\n"
                                f"**Before Nickname:** `{old_nick}`\n"
                                f"**After Nickname:** `{new_nick}`",
                    color=discord.Color.gold()
                )
                self.add_footer(embed)
                await mod_channel.send(embed=embed)

        # Global Name / Username Changes (⚡┆MODERATOR-ONLY)
        if before.name != after.name or before.global_name != after.global_name:
            mod_channel = self.get_log_channel(before.guild, ["moderator_only", "moderator_logs", "mod_logs"])
            if mod_channel:
                embed = discord.Embed(
                    title="👤 User Profile Name Changed",
                    description=f"**User:** {after.mention} (`{after.id}`)\n"
                                f"**Before Username:** `{before.name}` ({before.global_name or 'None'})\n"
                                f"**After Username:** `{after.name}` ({after.global_name or 'None'})",
                    color=discord.Color.purple()
                )
                self.add_footer(embed)
                await mod_channel.send(embed=embed)

    # ── 3. Server Logs (⚡┆SERVER-LOGS: Channels, Roles, Messages) ─
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="📁 Channel Created",
                description=f"**Channel:** {channel.mention} (`#{channel.name}`)\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.green()
            )
            self.add_footer(embed)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="🗑️ Channel Deleted",
                description=f"**Channel Name:** `#{channel.name}`\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.red()
            )
            self.add_footer(embed)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        log_ch = self.get_log_channel(message.guild, ["server_logs"])
        if log_ch and log_ch.id != message.channel.id:
            embed = discord.Embed(
                title="💬 Message Deleted",
                description=f"🗑️ **Message sent by {message.author.mention} deleted in {message.channel.mention}**\n\n"
                            f"**Content:**\n{message.content or '*No text content (attachment/embed)*'}",
                color=discord.Color.orange()
            )
            self.add_footer(embed, author=message.author)
            await log_ch.send(embed=embed)

    # ── 4. Moderator Logs (⚡┆MODERATOR-ONLY: VC Join & Leave) ──
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        mod_ch = self.get_log_channel(member.guild, ["moderator_only", "moderator_logs", "mod_logs"])
        if not mod_ch:
            return

        # Joined VC
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"🔊 **joined voice channel** `{after.channel.name}`",
                color=discord.Color.green()
            )
            self.add_footer(embed)
            await mod_ch.send(embed=embed)

        # Left VC
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"🔇 **left voice channel** `{before.channel.name}`",
                color=discord.Color.red()
            )
            self.add_footer(embed)
            await mod_ch.send(embed=embed)

        # Moved VC
        elif before.channel != after.channel:
            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"🔄 **moved voice channel** from `{before.channel.name}` to `{after.channel.name}`",
                color=discord.Color.blue()
            )
            self.add_footer(embed)
            await mod_ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerLogging(bot))
