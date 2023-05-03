import discord
from discord.ext import commands

class Deleteme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Deleteme.py is ready")
    
    # delete message
    @commands.command()
    async def deleteme(self, ctx, description = "bot responds and then deletes both own and user messages"):
        await ctx.send('I will delete myself in 3 seconds...', delete_after=3.0)
        await ctx.message.delete()
        
async def setup(bot):
    await bot.add_cog(Deleteme(bot))