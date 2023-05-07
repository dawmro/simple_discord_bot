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
    
    
class ZET_ETC_Pool_Accounts:
    def __init__(self):
        self.api_url = 'https://etc.zet-tech.eu'
        self.headers = {
            'Accepts': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(self.headers)
               
    def getAccountsData(self, wallet):
        url = self.api_url + '/api/accounts/'+wallet
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
    async def block(self, ctx, description = "get info about latest ETC block mined by pool, usage example: !block"):
    
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
        
        embed_message = discord.Embed(title = f"LATEST BLOCK INFO", description = f"For ETC ZETpool", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/block/{hash}/transactions")
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
    
    # get block info    
    @commands.command(aliases=["payout"])
    async def payment(self, ctx, wallet: str, description = "get info about latest payout to given ETC wallet, usage example: !block 0x6030c8112e68396416e98f8eeaabfade426e472b"):
    
        wallet_payments = ZET_ETC_Pool_Accounts()
        wallet_payments_data = wallet_payments.getAccountsData(wallet)

        latest_payments = wallet_payments_data['payments'][0]
        amount = latest_payments['amount'] / (10**9)
        tx = latest_payments['tx']
        timestamp = latest_payments['timestamp']
        dt_object = datetime.fromtimestamp(timestamp)
        
        embed_message = discord.Embed(title = f"LATEST PAYMENT INFO", description = f"Wallet: {wallet}", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/tx/{tx}")
        embed_message.set_author(name = f"Requested by {ctx.author}", icon_url = ctx.author.avatar)
        embed_message.add_field(name = "TX:", value = f"{tx}", inline = False) 
        embed_message.add_field(name = "Amount:", value = f"{amount} ETC", inline = True) 
        embed_message.set_footer(text = f"@{dt_object}") 
        
        await ctx.channel.send(embed = embed_message, delete_after=60.0)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(ZET_ETCPool(bot))
    
  