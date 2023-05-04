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
        await ctx.message.delete()
    
    # error message if user has no permissions
    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed_message = discord.Embed(title = f"{error}", color = discord.Color.red())
            embed_message.set_author(name = f"Warning triggered by {ctx.author}", icon_url = ctx.author.avatar)
            embed_message.set_image(url = "https://media.tenor.com/IS74NONBpy4AAAAC/abraxas-lotr.gif")
            
            await ctx.channel.send(embed = embed_message, delete_after=60.0)
            await ctx.message.delete()
    
    
async def setup(bot):
    await bot.add_cog(Moderation(bot))