import discord
from discord.ext import commands
         

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Moderation.py is ready")
    
    # clear messages    
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    async def clear(self, ctx, count: int, description = "remove number of messages from chat, usage example: !clear 10"):
        await ctx.channel.purge(limit = count)
        await ctx.channel.send(f"{count} messages has been deleted", delete_after=60.0)
        # fix for 404 NOT FOUND (error code : 1008)
        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)
        await msg.delete()
    
async def setup(bot):
    await bot.add_cog(Moderation(bot))