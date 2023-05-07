import discord
from discord.ext import commands
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

class ZET_ETC_Pool_Blocks:
    def __init__(self):
        self.api_url = 'https://etc.zet-tech.eu'
        self.headers = {
            'Accepts': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(self.headers)
               
    def getBlocksData(self):
        url = self.api_url + '/api/blocks'
        try:
            r = self.session.get(url)
            data = r.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
            

class ZET_ETCPool(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("ZET_ETCPool.py is ready")
    
    # get block info    
    @commands.command()
    async def block(self, ctx, description = "get info about latest ETC block mined by pool, usage: !block"):
        
        pool_blocks = ZET_ETC_Pool_Blocks()
        pool_blocks_data = pool_blocks.getBlocksData()
        latest_matured = pool_blocks_data['matured'][0]
        hash = latest_matured['hash']
        height = latest_matured['height']
        orphan = latest_matured['orphan']
        uncle = latest_matured['uncle']
        reward = latest_matured['reward'] / (10**9)
        variance = int(round(latest_matured['variance'] * 100))
        timestamp = latest_matured['timestamp']
        dt_object = datetime.fromtimestamp(timestamp)
        embed_message = discord.Embed(title = f"LATEST BLOCK INFO", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/block/{hash}/transactions")
        embed_message.set_author(name = f"Requested by {ctx.author}", icon_url = ctx.author.avatar)
        embed_message.add_field(name = "Hash:", value = f"{hash}", inline = False) 
        embed_message.add_field(name = "Height:", value = f"{height}", inline = True) 
        embed_message.add_field(name = "Orphan:", value = f"{orphan}", inline = True)
        embed_message.add_field(name = "Uncle:", value = f"{uncle}", inline = True)
        embed_message.add_field(name = "Reward:", value = f"{reward} ETC", inline = True)
        embed_message.add_field(name = "Variance:", value = f"{variance}%", inline = True)
        embed_message.set_footer(text = f"@{dt_object}") 
        
        await ctx.channel.send(embed = embed_message, delete_after=60.0)
        await ctx.message.delete()
   
   
async def setup(bot):
    await bot.add_cog(ZET_ETCPool(bot))