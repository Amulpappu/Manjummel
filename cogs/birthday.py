import discord
from discord.ext import commands, tasks
import json
import os
import datetime
import config

class Birthday(commands.Cog):
    """WishWave-style Birthday Bot with Wish Cards & Birthday Star Roles."""

    def __init__(self, bot):
        self.bot = bot
        self.birthdays = self.load_birthdays()
        self.bday_config = self.load_bday_config()
        self.birthday_check_loop.start()

    def cog_unload(self):
        self.birthday_check_loop.cancel()

    def load_birthdays(self):
        if os.path.exists(config.BIRTHDAYS_FILE):
            try:
                with open(config.BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_birthdays(self):
        with open(config.BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.birthdays, f, indent=4)

    def load_bday_config(self):
        file_path = os.path.join(config.DATA_DIR, "birthday_config.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_bday_config(self):
        file_path = os.path.join(config.DATA_DIR, "birthday_config.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.bday_config, f, indent=4)

    @commands.command(name="setbirthday")
    async def set_birthday(self, ctx, date_str: str):
        """Sets your birthday in MM-DD format. Usage: !setbirthday 07-25"""
        try:
            parsed = datetime.datetime.strptime(date_str, "%m-%d")
            formatted_date = parsed.strftime("%m-%d")
            user_id_str = str(ctx.author.id)
            if user_id_str not in self.birthdays:
                self.birthdays[user_id_str] = {}

            self.birthdays[user_id_str]["name"] = ctx.author.display_name
            self.birthdays[user_id_str]["date"] = formatted_date
            self.save_birthdays()

            await ctx.send(f"🎂 WishWave Birthday saved for {ctx.author.mention}: **{formatted_date}**!")
        except ValueError:
            await ctx.send("❌ Invalid date format! Please use `MM-DD` format (e.g. `07-25` for July 25).")

    @commands.command(name="setbirthdaymsg")
    async def set_birthday_msg(self, ctx, *, message: str):
        """Sets a custom personal birthday wish message. Usage: !setbirthdaymsg Hope all your wishes come true!"""
        user_id_str = str(ctx.author.id)
        if user_id_str not in self.birthdays:
            self.birthdays[user_id_str] = {"date": "01-01"}
        self.birthdays[user_id_str]["custom_msg"] = message
        self.save_birthdays()
        await ctx.send(f"💌 Personal Birthday Wish message saved for {ctx.author.mention}!")

    @commands.command(name="setbirthdayrole")
    @commands.has_permissions(administrator=True)
    async def set_birthday_role(self, ctx, role: discord.Role):
        """Sets the special Birthday Star role assigned to users on their birthday."""
        self.bday_config["role_id"] = role.id
        self.save_bday_config()
        await ctx.send(f"👑 Birthday Star role set to **{role.name}**!")

    @commands.command(name="listbirthdays")
    async def list_birthdays(self, ctx):
        """Lists all registered birthdays."""
        if not self.birthdays:
            return await ctx.send("📅 No birthdays recorded yet. Use `!setbirthday MM-DD` to add yours!")

        embed = discord.Embed(title="🎂 WishWave Server Birthdays", color=discord.Color.purple())
        for user_id, info in self.birthdays.items():
            user = self.bot.get_user(int(user_id))
            display_name = user.display_name if user else info.get("name", f"User {user_id}")
            embed.add_field(name=display_name, value=f"🗓️ `{info.get('date', 'Unknown')}`", inline=True)

        await ctx.send(embed=embed)

    @tasks.loop(hours=24)
    async def birthday_check_loop(self):
        """WishWave daily background check posting celebration Wish Cards & assigning Birthday Star role."""
        await self.bot.wait_until_ready()
        today_str = datetime.datetime.now().strftime("%m-%d")
        
        for user_id, info in self.birthdays.items():
            if info.get("date") == today_str:
                for guild in self.bot.guilds:
                    member = guild.get_member(int(user_id))
                    if member:
                        # Assign Birthday Role if configured
                        role_id = self.bday_config.get("role_id")
                        if role_id:
                            role = guild.get_role(int(role_id))
                            if role:
                                try:
                                    await member.add_roles(role, reason="Birthday Star Today!")
                                except Exception:
                                    pass

                        ch_id = config.ANNOUNCEMENT_CHANNEL_ID or config.WELCOME_CHANNEL_ID
                        channel = guild.get_channel(ch_id) if ch_id else guild.system_channel
                        if channel:
                            custom_note = info.get("custom_msg", "Wishing you a joyful day filled with happiness and laughter! ✨")
                            
                            embed = discord.Embed(
                                title="🎉 HAPPY BIRTHDAY! 🎂🎈",
                                description=f"Today we celebrate **{member.mention}**'s special day!\n\n💬 *\"{custom_note}\"*",
                                color=discord.Color.gold()
                            )
                            embed.set_thumbnail(url=member.display_avatar.url)
                            embed.set_footer(text="WishWave Birthday Celebration")
                            await channel.send(content=f"🥳 @everyone Let's wish **{member.display_name}** a Happy Birthday! 🎁✨", embed=embed)

    @birthday_check_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Birthday(bot))
