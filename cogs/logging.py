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
    """Comprehensive Discord Audit & Event Logging Cog for Manjummel Bot."""

    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild: discord.Guild, target_names: list[str]):
        """Helper to find a log channel by name (fuzzy match across formatted names)."""
        for channel in guild.text_channels:
            name_clean = channel.name.lower().replace("⚡┆", "").replace("📋┆", "").replace("🎭┆", "").replace("⚙️┆", "").replace("🛡️┆", "").replace("-", "_")
            # Explicitly exclude staff text channel #moderator-only from receiving log spam
            if "moderator_only" in name_clean or "mod_only" in name_clean:
                continue

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

    async def get_audit_log_entry(self, guild: discord.Guild, action: discord.AuditLogAction, target_id: int = None):
        """Fetches the latest audit log entry for a specific action and target user/role/channel."""
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if target_id is None or (entry.target and entry.target.id == target_id):
                    now = datetime.datetime.now(datetime.timezone.utc)
                    entry_time = entry.created_at
                    if (now - entry_time).total_seconds() < 15:
                        return entry
        except Exception:
            pass
        return None

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
            ("⚡┆ROLE-LOGS", "Audit logs for role assignments, permission edits, and role changes."),
            ("⚡┆SERVER-LOGS", "Audit logs for channel creations, deletions, and message deletions."),
            ("⚡┆MODERATOR-LOGS", "Audit logs for voice channel activity, mutes, deafens, timeouts, and nickname changes."),
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

            # Auto-assign @family role so member can access text/VC channels
            family_role = discord.utils.get(member.guild.roles, name="family")
            if not family_role:
                for r in member.guild.roles:
                    if "family" in r.name.lower():
                        family_role = r
                        break
            if family_role:
                try:
                    await member.add_roles(family_role, reason="Auto-assigned @family role on join")
                except Exception as e:
                    print(f"[Auto-Role Error] Could not assign @family role: {e}")

            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"{member.mention} **joined the server.** (Role: {family_role.mention if family_role else 'None'})\n\n"
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

    # ── 2. Role, Nickname & Timeout Logs (⚡┆ROLE-LOGS & ⚡┆MODERATOR-ONLY) ─
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = before.guild

        # Role Changes (⚡┆ROLE-LOGS)
        if before.roles != after.roles:
            role_channel = self.get_log_channel(guild, ["role_logs"])
            if role_channel:
                added_roles = [r.mention for r in after.roles if r not in before.roles]
                removed_roles = [r.mention for r in before.roles if r not in after.roles]

                entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_role_update, after.id)
                mod_str = f"\n**Responsible Moderator:** {entry.user.mention} (`{entry.user.name}`)" if entry and entry.user else ""

                if added_roles:
                    embed = discord.Embed(
                        title="🎭 Role Assigned",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Added Role(s):** {', '.join(added_roles)}{mod_str}",
                        color=discord.Color.blue()
                    )
                    self.add_footer(embed, author=entry.user if entry else None)
                    await role_channel.send(embed=embed)

                if removed_roles:
                    embed = discord.Embed(
                        title="🎭 Role Removed",
                        description=f"**User:** {after.mention} (`{after.id}`)\n"
                                    f"**Removed Role(s):** {', '.join(removed_roles)}{mod_str}",
                        color=discord.Color.orange()
                    )
                    self.add_footer(embed, author=entry.user if entry else None)
                    await role_channel.send(embed=embed)

        # Server Nickname Changes (⚡┆MODERATOR-LOGS)
        if before.nick != after.nick:
            mod_channel = self.get_log_channel(guild, ["moderator_logs", "mod_logs", "server_logs"])
            if mod_channel:
                old_nick = before.nick if before.nick else "None (No Nickname)"
                new_nick = after.nick if after.nick else "None (Reset to Username)"

                entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_update, after.id)
                mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user and entry.user.id != after.id) else "Self (User)"

                embed = discord.Embed(
                    title="✏️ Server Nickname Changed",
                    description=f"**Target User:** {after.mention} (`{after.id}`)\n"
                                f"**Before Nickname:** `{old_nick}`\n"
                                f"**After Nickname:** `{new_nick}`\n"
                                f"**Changed By (Moderator):** {mod_str}",
                    color=discord.Color.gold()
                )
                self.add_footer(embed, author=entry.user if (entry and entry.user) else None)
                await mod_channel.send(embed=embed)

        # Timeout Logs (⚡┆MODERATOR-LOGS)
        if before.timed_out_until != after.timed_out_until:
            mod_channel = self.get_log_channel(guild, ["moderator_logs", "mod_logs", "server_logs"])
            if mod_channel:
                entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_update, after.id)
                mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Unknown Moderator"

                if after.timed_out_until and after.timed_out_until > datetime.datetime.now(datetime.timezone.utc):
                    ts = int(after.timed_out_until.timestamp())
                    embed = discord.Embed(
                        title="⏳ Member Timed Out",
                        description=f"**Target User:** {after.mention} (`{after.id}`)\n"
                                    f"**Responsible Moderator:** {mod_str}\n"
                                    f"**Timed Out Until:** <t:{ts}:F> (<t:{ts}:R>)",
                        color=discord.Color.red()
                    )
                    self.add_footer(embed, author=entry.user if entry else None)
                    await mod_channel.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="⏱️ Timeout Removed",
                        description=f"**Target User:** {after.mention} (`{after.id}`)\n"
                                    f"**Responsible Moderator:** {mod_str}",
                        color=discord.Color.green()
                    )
                    self.add_footer(embed, author=entry.user if entry else None)
                    await mod_channel.send(embed=embed)

        # Global Name / Username Changes (⚡┆MODERATOR-LOGS)
        if before.name != after.name or before.global_name != after.global_name:
            mod_channel = self.get_log_channel(guild, ["moderator_logs", "mod_logs", "server_logs"])
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

    # ── 3. Role Creation / Update / Deletion Logs (⚡┆ROLE-LOGS) ─
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        log_ch = self.get_log_channel(role.guild, ["role_logs", "server_logs"])
        if log_ch:
            entry = await self.get_audit_log_entry(role.guild, discord.AuditLogAction.role_create, role.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            embed = discord.Embed(
                title="🎭 Role Created",
                description=f"**Role:** {role.mention} (`{role.name}`)\n"
                            f"**Created By (Moderator):** {mod_str}\n"
                            f"**ID:** `{role.id}`",
                color=discord.Color.green()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        log_ch = self.get_log_channel(role.guild, ["role_logs", "server_logs"])
        if log_ch:
            entry = await self.get_audit_log_entry(role.guild, discord.AuditLogAction.role_delete, role.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            embed = discord.Embed(
                title="🗑️ Role Deleted",
                description=f"**Role Name:** `{role.name}`\n"
                            f"**Deleted By (Moderator):** {mod_str}\n"
                            f"**ID:** `{role.id}`",
                color=discord.Color.red()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        log_ch = self.get_log_channel(after.guild, ["role_logs", "server_logs"])
        if log_ch and (before.name != after.name or before.color != after.color or before.permissions != after.permissions):
            entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.role_update, after.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"

            changes = []
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` ➔ `{after.name}`")
            if before.color != after.color:
                changes.append(f"**Color:** `{before.color}` ➔ `{after.color}`")
            if before.permissions != after.permissions:
                changes.append(f"**Permissions Modified**")

            embed = discord.Embed(
                title="🎭 Role Modified",
                description=f"**Role:** {after.mention} (`{after.id}`)\n"
                            f"**Modified By (Moderator):** {mod_str}\n" + "\n".join(changes),
                color=discord.Color.gold()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await log_ch.send(embed=embed)

    # ── 4. Channel Creation, Deletion & Permission Logs (⚡┆SERVER-LOGS & ⚡┆ROLE-LOGS) ─
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server_logs"])
        if log_ch:
            entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_create, channel.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            embed = discord.Embed(
                title="📁 Channel Created",
                description=f"**Channel:** {channel.mention} (`#{channel.name}`)\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**Created By (Moderator):** {mod_str}\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.green()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_ch = self.get_log_channel(channel.guild, ["server_logs"])
        if log_ch:
            entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            embed = discord.Embed(
                title="🗑️ Channel Deleted",
                description=f"**Channel Name:** `#{channel.name}`\n"
                            f"**Type:** `{str(channel.type).upper()}`\n"
                            f"**Deleted By (Moderator):** {mod_str}\n"
                            f"**ID:** `{channel.id}`",
                color=discord.Color.red()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        guild = after.guild
        log_ch = self.get_log_channel(guild, ["role_logs", "server_logs"])
        if not log_ch:
            return

        # Check Channel Permission Overwrite Modifications
        if before.overwrites != after.overwrites:
            entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.channel_overwrite_update, after.id)
            if not entry:
                entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.channel_overwrite_create, after.id)
            if not entry:
                entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.channel_overwrite_delete, after.id)

            mod_str = f"{entry.user.mention}" if (entry and entry.user) else "@Moderator"

            allowed_perms = []
            denied_perms = []
            target_mention = "`Role/User`"
            target_id = "N/A"

            for target, overwrite in after.overwrites.items():
                old_overwrite = before.overwrites.get(target)
                if old_overwrite != overwrite:
                    target_mention = target.mention
                    target_id = target.id
                    for perm, value in overwrite:
                        old_val = getattr(old_overwrite, perm, None) if old_overwrite else None
                        if value != old_val:
                            if value is True:
                                allowed_perms.append(perm.replace("_", " ").title())
                            elif value is False:
                                denied_perms.append(perm.replace("_", " ").title())

            desc = f"{mod_str} **has modified channel permissions for** {target_mention} **in** {after.mention}\n\n"
            if allowed_perms:
                desc += f"**Allowed Permissions**\n" + "\n".join([f"✅ `{p}`" for p in allowed_perms]) + "\n\n"
            if denied_perms:
                desc += f"**Denied Permissions**\n" + "\n".join([f"❌ `{p}`" for p in denied_perms]) + "\n\n"
            desc += f"**IDs**\n`{after.mention}` (`{after.id}`)\n`{target_mention}` (`{target_id}`)\n`{mod_str}` (`{getattr(entry.user, 'id', 'N/A') if entry else 'N/A'}`)"

            embed = discord.Embed(
                description=desc,
                color=discord.Color.gold()
            )
            self.add_footer(embed, author=entry.user if entry else None)
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

    # ── 5. Moderator Logs (⚡┆MODERATOR-LOGS: VC Join, Leave, Mute, Deafen, Disconnect) ──
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        mod_ch = self.get_log_channel(guild, ["moderator_logs", "mod_logs", "server_logs"])
        if not mod_ch:
            return

        # Server Mute Updates
        if before.mute != after.mute:
            entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_update, member.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            status_str = "Server Muted 🎙️" if after.mute else "Server Unmuted 🎙️"

            embed = discord.Embed(
                title=f"🎙️ Voice {status_str}",
                description=f"**Target User:** {member.mention} (`{member.id}`)\n"
                            f"**Action:** {status_str}\n"
                            f"**Responsible Moderator:** {mod_str}",
                color=discord.Color.red() if after.mute else discord.Color.green()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await mod_ch.send(embed=embed)

        # Server Deafen Updates
        if before.deaf != after.deaf:
            entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_update, member.id)
            mod_str = f"{entry.user.mention} (`{entry.user.name}`)" if (entry and entry.user) else "Moderator / System"
            status_str = "Server Deafened 🎧" if after.deaf else "Server Undeafened 🎧"

            embed = discord.Embed(
                title=f"🎧 Voice {status_str}",
                description=f"**Target User:** {member.mention} (`{member.id}`)\n"
                            f"**Action:** {status_str}\n"
                            f"**Responsible Moderator:** {mod_str}",
                color=discord.Color.red() if after.deaf else discord.Color.green()
            )
            self.add_footer(embed, author=entry.user if entry else None)
            await mod_ch.send(embed=embed)

        # Joined VC
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                description=f"**{member.name}**\n"
                            f"🔊 **joined voice channel** `{after.channel.name}`",
                color=discord.Color.green()
            )
            self.add_footer(embed)
            await mod_ch.send(embed=embed)

        # Left or Disconnected VC
        elif before.channel is not None and after.channel is None:
            entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.member_disconnect, member.id)
            if entry and entry.user and entry.user.id != member.id:
                embed = discord.Embed(
                    title="🔌 Disconnected from Voice Channel",
                    description=f"**Target User:** {member.mention} (`{member.id}`)\n"
                                f"**Channel:** `{before.channel.name}`\n"
                                f"**Disconnected By (Moderator):** {entry.user.mention} (`{entry.user.name}`)",
                    color=discord.Color.dark_red()
                )
                self.add_footer(embed, author=entry.user)
            else:
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
