import discord
from discord.ext import commands, tasks
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import asyncio
 
 
cached_block_file = Path("data/json/cached_block.json")
if not os.path.exists(cached_block_file):
        with open(cached_block_file, "w+") as f:
            f.write("{}") 
    
class ZET_ETC:
    def __init__(self):
        self.api_url = 'https://etc.zet-tech.eu'
        self.headers = {
            'Accepts': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(self.headers)
    
    # get json for blocks 
    def getBlocksData(self):
        url = self.api_url + '/api/blocks'
        try:
            r = self.session.get(url)
            data = r.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
    
    # get json for account
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
        # load cached block info from file
        with open(cached_block_file, "r") as f:
            try:
                self.cached_block = json.load(f)
            except JSONDecodeError:
                pass
        self.new_block_check.start()
        self.bot.loop.create_task(self.save_cached())
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("ZET_ETCPool.py is ready")
             
    # save current block height to cached block file    
    async def save_cached(self):    
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            with open(cached_block_file, "w") as f:
                json.dump(self.cached_block, f, indent=4)    
            # prevent crashes
            await asyncio.sleep(5)    
        
    # check for new block    
    @tasks.loop(seconds = 10)
    async def new_block_check(self):
        # add dummy block height to cached block if not present
        if not "height" in self.cached_block: 
            self.cached_block["height"] = 999999999999
        
        zet_etc = ZET_ETC()
        pool_blocks_data = zet_etc.getBlocksData()
        
        latest_matured = pool_blocks_data['matured'][0]
        hash = latest_matured['hash']
        height = latest_matured['height']
        orphan = latest_matured['orphan']
        uncle = latest_matured['uncle']
        reward = latest_matured['reward'] / (10**9)
        variance = int(round(latest_matured['variance'] * 100))
        timestamp = latest_matured['timestamp']
        dt_object = datetime.fromtimestamp(timestamp)
        
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if height > self.cached_block["height"]:
                    embed_message = discord.Embed(title = f"NEW BLOCK!", description = f"For ETC ZETpool", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/block/{hash}/transactions")
                    embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
                    embed_message.add_field(name = "Hash:", value = f"{hash}", inline = False) 
                    embed_message.add_field(name = "Height:", value = f"{height}", inline = True) 
                    embed_message.add_field(name = "Orphan:", value = f"{orphan}", inline = True)
                    embed_message.add_field(name = "Uncle:", value = f"{uncle}", inline = True)
                    embed_message.add_field(name = "Reward:", value = f"{reward} ETC", inline = True)
                    embed_message.add_field(name = "Variance:", value = f"{variance}%", inline = True)
                    embed_message.set_footer(text = f"@{dt_object}") 
                    
                    await channel.send(embed = embed_message)
                else:
                    await channel.send(self.cached_block["height"])
                    
        # cache current block height
        self.cached_block["height"] = height 
        
    # get block info    
    @commands.command()
    async def block(self, ctx, description = "get info about latest ETC block mined by pool, usage example: !block"):
    
        zet_etc = ZET_ETC()
        pool_blocks_data = zet_etc.getBlocksData()
        
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
        embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
        embed_message.add_field(name = "Hash:", value = f"{hash}", inline = False) 
        embed_message.add_field(name = "Height:", value = f"{height}", inline = True) 
        embed_message.add_field(name = "Orphan:", value = f"{orphan}", inline = True)
        embed_message.add_field(name = "Uncle:", value = f"{uncle}", inline = True)
        embed_message.add_field(name = "Reward:", value = f"{reward} ETC", inline = True)
        embed_message.add_field(name = "Variance:", value = f"{variance}%", inline = True)
        embed_message.set_footer(text = f"@{dt_object}") 
        
        await ctx.channel.send(embed = embed_message, delete_after=60.0)
        await ctx.message.delete()
        
        
        

    
    # get payment info    
    @commands.command(aliases=["payout"])
    async def payment(self, ctx, wallet: str, description = "get info about latest payout to given ETC wallet, usage example: !payment 0x6030c8112e68396416e98f8eeaabfade426e472b"):
    
        zet_etc = ZET_ETC()
        wallet_payments_data = zet_etc.getAccountsData(wallet)

        latest_payments = wallet_payments_data['payments'][0]
        amount = latest_payments['amount'] / (10**9)
        tx = latest_payments['tx']
        timestamp = latest_payments['timestamp']
        dt_object = datetime.fromtimestamp(timestamp)
        
        embed_message = discord.Embed(title = f"LATEST PAYMENT INFO", description = f"Wallet: {wallet}", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/tx/{tx}")
        embed_message.set_author(name = f"Requested by {ctx.author}", icon_url = ctx.author.avatar)
        embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
        embed_message.add_field(name = "TX:", value = f"{tx}", inline = False) 
        embed_message.add_field(name = "Amount:", value = f"{amount} ETC", inline = True) 
        embed_message.set_footer(text = f"@{dt_object}") 
        
        await ctx.channel.send(embed = embed_message, delete_after=60.0)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(ZET_ETCPool(bot))
    
  