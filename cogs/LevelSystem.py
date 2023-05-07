import discord
from discord.ext import commands
import asyncio
import math
import json
from json.decoder import JSONDecodeError
import random

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.save())
        
        # load users info from file
        with open("data/json/user_level_system.json", "r") as f:
            try:
                self.users = json.load(f)
            except JSONDecodeError:
                pass
            
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("LevelSystem.py is ready")
    
    # save user info
    async def save(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            with open("data/json/user_level_system.json", "w") as f:
                json.dump(self.users, f, indent=4)

            # prevent crashes
            await asyncio.sleep(5)
    
    # calculate exp needed for next level
    def next_lvl_exp(self, current_level):
        return math.ceil(((3 * (current_level ** 3)) / 1.5) + 20)
    
    # add lexel to user    
    def level_up(self, author_id):
        current_exp = self.users[author_id]["Experience"]
        current_level = self.users[author_id]["Level"]
        if current_exp >= self.next_lvl_exp(current_level):
            self.users[author_id]["Level"] += 1
            return True
        else:
            return False
            
    # trigger on new message
    @commands.Cog.listener()
    async def on_message(self, message):
        # get user id
        author_id = str(message.author.id)
        
        # add user to list of user if not present
        if not author_id in self.users: 
            self.users[author_id] = {}
            self.users[author_id]["Level"] = 1
            self.users[author_id]["Experience"] = 0
        
        # add exp to user    
        random_exp = random.randint(3, 7)
        self.users[author_id]["Experience"] += random_exp
        
        # check if user levels up
        if self.level_up(author_id):
            level_up_embed = discord.Embed(title="Level Up!", color=discord.Color.blue())
            level_up_embed.add_field(name="Congratulations", value=f"{message.author.mention} has just leveled up to level {self.users[author_id]['Level']}!")
            await message.channel.send(embed=level_up_embed, delete_after=60.0)
    
    # check current level / exp
    @commands.command(aliases=["lvl", "experience", "exp"])
    async def level(self, ctx, user: discord.User=None):
        # check own level
        if user is None:
            user = ctx.author
        # check level of a given user
        elif user is not None:
            user = user
            
        user_lvl = self.users[str(user.id)]["Level"]
        user_exp = self.users[str(user.id)]["Experience"]
        user_exp_needed_for_next_lvl = self.next_lvl_exp(user_lvl) - user_exp
 
        level_card = discord.Embed(title=f"{user}'s Stats:", color=discord.Color.yellow())
        level_card.set_author(name = f"Requested by {ctx.author}", icon_url = ctx.author.avatar)
        level_card.add_field(name="Level:", value = user_lvl)
        level_card.add_field(name="Experience:", value = user_exp)
        level_card.set_footer(text=f"Experience needed to level up: {user_exp_needed_for_next_lvl}")
        
        await ctx.send(embed=level_card, delete_after=60.0)
    
    
async def setup(bot):
    await bot.add_cog(LevelSystem(bot))