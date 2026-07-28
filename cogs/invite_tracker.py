import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os
import config


class InviteTracker(commands.Cog):
    """Cog for tracking server invites, who invited whom, and invite leaderboards."""

    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}
        self.invite_data = self.load_invite_data()

    async def cog_load(self):
        """Schedule initial cache building as a background task after bot is ready."""
        asyncio.create_task(self._init_invites_cache())

    async def _init_invites_cache(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
            except discord.Forbidden:
                print(f"[InviteTracker] Lacking Manage Server permissions in {guild.name}")
            except Exception as e:
                print(f"[InviteTracker] Error fetching invites for {guild.name}: {e}")


    def load_invite_data(self):
        file_path = os.path.join(config.DATA_DIR, "invites.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_invite_data(self):
        file_path = os.path.join(config.DATA_DIR, "invites.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.invite_data, f, indent=4)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Update invite cache when a new invite is created."""
        if invite.guild.id not in self.invites_cache:
            self.invites_cache[invite.guild.id] = {}
        self.invites_cache[invite.guild.id][invite.code] = invite.uses

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Remove invite from cache when deleted."""
        if invite.guild.id in self.invites_cache:
            self.invites_cache[invite.guild.id].pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Find matching invite code used by new member."""
        guild = member.guild
        if guild.id not in self.invites_cache:
            return

        old_invites = self.invites_cache[guild.id]
        inviter = None
        used_code = None

        try:
            new_invites = await guild.invites()
            for invite in new_invites:
                if invite.code in old_invites:
                    if invite.uses > old_invites[invite.code]:
                        inviter = invite.inviter
                        used_code = invite.code
                        break

            # Update cache
            self.invites_cache[guild.id] = {inv.code: inv.uses for inv in new_invites}
        except Exception as e:
            print(f"[InviteTracker] Error matching invite on join: {e}")

        if inviter:
            inviter_id_str = str(inviter.id)
            if inviter_id_str not in self.invite_data:
                self.invite_data[inviter_id_str] = {"total": 0, "real": 0, "fake": 0, "left": 0}

            self.invite_data[inviter_id_str]["total"] += 1
            self.invite_data[inviter_id_str]["real"] += 1
            self.save_invite_data()

            # Announce in welcome channel if available
            ch_id = config.WELCOME_CHANNEL_ID or config.ANNOUNCEMENT_CHANNEL_ID
            channel = guild.get_channel(ch_id) if ch_id else guild.system_channel
            if channel:
                stats = self.invite_data[inviter_id_str]
                embed = discord.Embed(
                    title="🎉 Member Joined via Invite!",
                    description=f"{member.mention} joined using invite code `{used_code}` created by **{inviter.display_name}**!\n"
                                f"👤 **{inviter.display_name}** now has **{stats['real']}** invites ({stats['total']} total).",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed)

    @commands.hybrid_command(name="invites", description="Displays invite statistics for a user.")
    @app_commands.describe(member="Optional member to check invite stats for")
    async def get_invites(self, ctx: commands.Context, member: discord.Member = None):
        """Displays invite statistics for a user."""
        target = member or ctx.author
        stats = self.invite_data.get(str(target.id), {"total": 0, "real": 0, "fake": 0, "left": 0})
        
        embed = discord.Embed(
            title=f"📩 Invite Statistics for {target.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Real Invites", value=f"`{stats['real']}`", inline=True)
        embed.add_field(name="Total Invites", value=f"`{stats['total']}`", inline=True)
        embed.add_field(name="Left Server", value=f"`{stats['left']}`", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="invitesleaderboard", aliases=["topinvites"], description="Displays top inviters in the server.")
    async def invites_leaderboard(self, ctx: commands.Context):
        """Displays top inviters in the server."""
        if not self.invite_data:
            return await ctx.send("📩 No invite data recorded yet.")

        sorted_users = sorted(self.invite_data.items(), key=lambda x: x[1].get("real", 0), reverse=True)
        
        description = ""
        rank = 1
        for user_id_str, stats in sorted_users[:10]:
            user = self.bot.get_user(int(user_id_str))
            name = user.display_name if user else f"User {user_id_str}"
            description += f"**#{rank}** {name} — `{stats['real']}` real invites ({stats['total']} total)\n"
            rank += 1

        embed = discord.Embed(
            title="🏆 Invite Leaderboard",
            description=description,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
