import discord
from discord.ext import commands
import datetime
import config

class ServerLogging(commands.Cog):
    """Comprehensive Discord Audit & Event Logging Cog for Manjummel Bot."""

    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild: discord.Guild, target_names: list[str]):
        """Helper to find a log channel by name (fuzzy match or exact match)."""
        for channel in guild.text_channels:
            name_lower = channel.name.lower()
            for target in target_names:
                if target.lower() in name_lower or name_lower in target.lower():
                    return channel
        return None

    # ── Automatic Channel Creation Command ───────────────────
    @commands.command(name="setupchannels", aliases=["createlogchannels"])
    @commands.has_permissions(administrator=True)
    async def setup_log_channels(self, ctx):
        """Automatically creates formatted announcement & audit log channels under a category."""
        guild = ctx.guild
        category_name = "📊 SERVER LOGS & CHANNELS"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            await ctx.send(f"📁 Created category **{category_name}**.")

        channels_to_create = [
            ("🎂┆ʙɪʀᴛʜᴅᴀʏ-ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ", "Channel for birthday celebration cards and wishes."),
            ("🙏┆ᴡᴇʟᴄᴏᴍᴇ", "Channel for welcoming new server members."),
            ("📋┆join-leave-logs", "Audit logs for member joins and leaves."),
            ("🎭┆role-logs", "Audit logs for member role additions and removals."),
            ("⚙️┆server-logs", "Audit logs for channels, roles, and deleted/edited messages."),
            ("🛡️┆moderator-logs", "Audit logs for voice channel joins/leaves and nickname changes."),
        ]

        created_count = 0
        for name, topic in channels_to_create:
            existing = discord.utils.get(guild.text_channels, name=name)
            if not existing:
                await guild.create_text_channel(name, category=category, topic=topic)
                created_count += 1

        await ctx.send(f"✅ Setup complete! Created `{created_count}` logging & announcement channels under **{category_name}**.")

    # ── 1. Join & Leave Logs (📋┆join-leave-logs) ───────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.get_log_channel(member.guild, ["join-leave-logs", "join_leave_logs", "join-logs"])
        if channel:
            account_created = int(member.created_at.timestamp())
            embed = discord.Embed(
                title="📥 Member Joined",
                description=f"**User:** {member.mention} (`{member.display_name}`)\n"
                            f"**User ID:** `{member.id}`\n"
                            f"**Account Created:** <t:{account_created}:R>\n"
                            f"**Total Server Members:** `{member.guild.member_count}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.get_log_channel(member.guild, ["join-leave-logs", "join_leave_logs", "leave-logs"])
        if channel:
            embed = discord.Embed(
                title="📤 Member Left",
                description=f"**User:** {member.mention} (`{member.display_name}`)\n"
                            f"**User ID:** `{member.id}`\n"
                            f"**Total Server Members:** `{member.guild.member_count}`",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    # ── 2. Role Logs & Member Updates (🎭┆role-logs & 🛡️┆moderator-logs)
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Role Changes (🎭┆role-logs)
        if before.roles != after.roles:
            role_channel = self.get_log_channel(before.guild, ["role-logs", "role_logs"])
            if role_channel:
                added_roles = [r.mention for r in after.roles if r not in before.roles]
                removed_roles = [r.mention for r in before.roles if r not in after.roles]

                if added_roles:
                    embed = discord.Embed(
                        title="🎭 Role Assigned",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Added Role(s):** {', '.join(added_roles)}",
                        color=discord.Color.blue(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    await role_channel.send(embed=embed)

                if removed_roles:
                    embed = discord.Embed(
                        title="🎭 Role Removed",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Removed Role(s):** {', '.join(removed_roles)}",
                        color=discord.Color.orange(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    await role_channel.send(embed=embed)

        # Nickname / Name Changes (🛡️┆moderator-logs)
        if before.nick != after.nick:
            mod_channel = self.get_log_channel(before.guild, ["moderator-logs", "mod-logs", "mod_logs"])
            if mod_channel:
                embed = discord.Embed(
                    title="✏️ Nickname Changed",
                    description=f"**User:** {after.mention} (`{after.id}`)\n"
                                f"**Before:** `{before.nick or before.name}`\n"
                                f"**After:** `{after.nick or after.name}`",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.utcnow()
                )
                await mod_channel.send(embed=embed)

    # ── 3. Server Logs (⚙️┆server-logs: Channels, Roles, Messages)
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server-logs", "server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="📁 Channel Created",
                description=f"**Channel:** {channel.mention} (`#{channel.name}`)\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server-logs", "server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="🗑️ Channel Deleted",
                description=f"**Channel Name:** `#{channel.name}`\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        log_ch = self.get_log_channel(role.guild, ["server-logs", "server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="🎭 Server Role Created",
                description=f"**Role:** {role.mention} (`{role.name}`)\n"
                            f"**ID:** `{role.id}`",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        log_ch = self.get_log_channel(role.guild, ["server-logs", "server_logs"])
        if log_ch:
            embed = discord.Embed(
                title="🗑️ Server Role Deleted",
                description=f"**Role Name:** `{role.name}`\n"
                            f"**ID:** `{role.id}`",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        log_ch = self.get_log_channel(message.guild, ["server-logs", "server_logs"])
        if log_ch and log_ch.id != message.channel.id:
            embed = discord.Embed(
                title="💬 Message Deleted",
                description=f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                            f"**Channel:** {message.channel.mention}\n\n"
                            f"**Content:**\n{message.content or '*No text content (attachment/embed)*'}",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_ch.send(embed=embed)

    # ── 4. Moderator Logs (🛡️┆moderator-logs: VC Join & Leave) ──
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        mod_ch = self.get_log_channel(member.guild, ["moderator-logs", "mod-logs", "mod_logs"])
        if not mod_ch:
            return

        # Joined VC
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 Joined Voice Channel",
                description=f"**User:** {member.mention} (`{member.id}`)\n"
                            f"**Channel:** {after.channel.name}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await mod_ch.send(embed=embed)

        # Left VC
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Left Voice Channel",
                description=f"**User:** {member.mention} (`{member.id}`)\n"
                            f"**Channel:** {before.channel.name}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await mod_ch.send(embed=embed)

        # Moved VC
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="🔄 Moved Voice Channel",
                description=f"**User:** {member.mention} (`{member.id}`)\n"
                            f"**From:** {before.channel.name}\n"
                            f"**To:** {after.channel.name}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            await mod_ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerLogging(bot))
