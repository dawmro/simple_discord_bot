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
        while not self.bot.is_close():
            with open("data/json/user_level_system.json", "w") as f:
                json.dumps(self.users, f, indent=4)

            # prevent crashes
            await asyncio.sleep(5)
            
    @commands.Cog.listener()
    async def on_message(self, message):
        # get user id
        author_id = str(message.author.id)
        
        # add user to list of user if not present
        if not author_id in self.users: 
            self.users[author_id] = {}
            self.users[author_id]["Level"] = 1
            self.users[author_id]["Experience"] = 0
            
    

    
        
async def setup(bot):
    await bot.add_cog(LevelSystem(bot))