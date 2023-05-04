import discord
from discord.ext import commands
import requests
import json


class Joke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # get joke via api    
    def get_joke(self):
        response = requests.get("https://api.chucknorris.io/jokes/random", timeout = 3)
        try:  
            joke = json.loads(response.text)['value']
        except:
            joke = "Why was 6 afraid of 7? Because 7,8,9."
        return joke    
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Joke.py is ready")
    
    # tell joke
    @commands.command()
    async def joke(self, ctx, description = "bot tells you joke"):
        joke = self.get_joke()
        await ctx.send(joke, delete_after=60.0)
        await ctx.message.delete()
        
async def setup(bot):
    await bot.add_cog(Joke(bot))