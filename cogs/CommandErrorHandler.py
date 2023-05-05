import discord
from discord.ext import commands
         

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("CommandErrorHandler.py is ready")
    
    # trigger at command error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
    
        embed_message = discord.Embed(title = f"{error}", color = discord.Color.red())
        embed_message.set_author(name = f"Error triggered by {ctx.author}", icon_url = ctx.author.avatar)
        
        if isinstance(error, commands.MissingPermissions):
            embed_message.set_image(url = "https://media.tenor.com/IS74NONBpy4AAAAC/abraxas-lotr.gif")
            
        await ctx.channel.send(embed = embed_message, delete_after=60.0)
        await ctx.message.delete()
           
    
    
async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))