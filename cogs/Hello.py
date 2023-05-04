import discord
from discord.ext import commands

class Hello(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Hello.py is ready")
    
    # say hello
    @commands.command()
    async def hello(self, ctx, description = "bot greets you and says your name"):
        await ctx.send(f"Hello {ctx.author}", delete_after=60.0)
        await ctx.message.delete()
        
async def setup(bot):
    await bot.add_cog(Hello(bot))