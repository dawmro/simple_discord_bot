import discord
from discord.ext import commands
import asyncio

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Countdown.py is ready")
    
    # countdown from 3 to 0
    @commands.command()
    async def countdown(self, ctx, description = "countdown from 3 to 0"):
        msg = await ctx.send('3')
        await asyncio.sleep(1.0)
        await msg.edit(content='2')
        await asyncio.sleep(1.0)
        await msg.edit(content='1')
        await asyncio.sleep(1.0)
        await msg.edit(content='GO!', delete_after=60.0)
        await ctx.message.delete()
        
async def setup(bot):
    await bot.add_cog(Countdown(bot))