import discord
from discord.ext import commands
from discord.utils import get


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["👍", "👎"]
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Poll.py is ready")
        
    @commands.command()
    async def poll(self, ctx, *, question):
        msg = await ctx.send(f"Poll: {question} -{ctx.author}")
        for name in self.reactions:
            emoji = get(ctx.guild.emojis, name=name)
            await msg.add_reaction(emoji or name) 
            
            
async def setup(bot):
    await bot.add_cog(Poll(bot))