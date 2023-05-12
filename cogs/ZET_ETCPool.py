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
            
cached_wallets_file = Path("data/json/cached_wallets.json")
if not os.path.exists(cached_wallets_file):
        with open(cached_wallets_file, "w+") as f:
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
        # load cached wallets info from file
        with open(cached_wallets_file, "r") as f:
            try:
                self.cached_wallets = json.load(f)
            except JSONDecodeError:
                pass
        self.new_block_check.start()
        self.new_payment_check.start()
        self.bot.loop.create_task(self.save_cached())
    
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("ZET_ETCPool.py is ready")
     
     
    # save current block height to cached block file    
    async def save_cached(self):    
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # save cached block
            with open(cached_block_file, "w") as f:
                json.dump(self.cached_block, f, indent=4)
            # save cached wallets
            with open(cached_wallets_file, "w") as f:
                json.dump(self.cached_wallets, f, indent=4)    
            # wait to prevent crashes
            await asyncio.sleep(5)    
    
    
    # add wallet to wallet_watch   
    @commands.command() 
    async def add_watch_wallet(self, ctx, wallet, description = "add wallet to watch list to get notifications, usage example: !add_watch_wallet 0x6030c8112e68396416e98f8eeaabfade426e472b"):
        # get user id
        author_id = str(ctx.author.id)
        # add new entry of user and his wallet to watch list if user not present
        if not author_id in self.cached_wallets: 
            self.cached_wallets[author_id] = {}
            self.cached_wallets[author_id]["Wallet"] = wallet
            await ctx.channel.send(f"Created New Watch_Wallet For A Wallet {wallet}!", delete_after=60.0)
        # add wallet to user wallet_watch if it is not already there   
        elif self.cached_wallets[author_id]["Wallet"] == wallet:
            await ctx.channel.send(f"Wallet {wallet} Already In Watch_Wallet!", delete_after=60.0)
        else:
            self.cached_wallets[author_id]["Wallet"] = wallet
            await ctx.channel.send(f"New Wallet {wallet} Added To Watch_Wallet!", delete_after=60.0)
        await ctx.message.delete()
    
    
    # remove wallet from wallet_watch   
    @commands.command() 
    async def remove_watch_wallet(self, ctx, description = "remove wallet from watch list and stop getting notifications, usage example: !remove_watch_wallet"):
        # get user id
        author_id = str(ctx.author.id)
        # if user not present do nothing 
        if not author_id in self.cached_wallets: 
            await ctx.channel.send("User Not Watching Any Wallet!", delete_after=60.0)
        # remove wallet and user from wallet_watch  
        else:
            wallet = self.cached_wallets.pop(author_id)
            await ctx.channel.send(f"Wallet {wallet['Wallet']} Removed From Watch_Wallet!", delete_after=60.0)
            await ctx.message.delete()
       
       
    # check watch_wallet status   
    @tasks.loop(seconds = 60)
    async def new_payment_check(self):
        # fix for AttributeError("'NoneType' object has no attribute 'send'")
        await self.bot.wait_until_ready()
        # create instance of a class
        zet_etc = ZET_ETC()
        # loop through every user having watch_wallet active
        for cached_user in self.cached_wallets:
            # get wallet info via api
            wallet_data = zet_etc.getAccountsData(self.cached_wallets[cached_user]['Wallet'])
            # get latest payment info
            latest_payments = wallet_data['payments'][0]
            # add new Payment entry if not present
            if not 'Payment' in self.cached_wallets[cached_user]:
                self.cached_wallets[cached_user]['Payment'] = latest_payments
            # compare timestamps cached and new payments     
            else:
                # create user from cached_user string
                user = self.bot.get_user(int(cached_user))
                # if latest payment timestmp is newer than cached one 
                if (latest_payments['timestamp'] > self.cached_wallets[cached_user]['Payment']['timestamp']): 
                    # inform user about new payout via private message
                    amount = latest_payments['amount'] / (10**9)
                    tx = latest_payments['tx']
                    timestamp = latest_payments['timestamp']
                    dt_object = datetime.fromtimestamp(timestamp)
                    embed_message = discord.Embed(title = f"NEW PAYMENT!", description = f"Wallet: {self.cached_wallets[cached_user]['Wallet']}", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/tx/{tx}")
                    embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
                    embed_message.add_field(name = "TX:", value = f"{tx}", inline = False) 
                    embed_message.add_field(name = "Amount:", value = f"{amount} ETC", inline = True) 
                    embed_message.set_footer(text = f"@{dt_object}")
                    await user.send(embed = embed_message)
                # cache current payment
                self.cached_wallets[cached_user]['Payment'] = latest_payments
    
    
    # check for new block    
    @tasks.loop(seconds = 60)
    async def new_block_check(self):
        await self.bot.wait_until_ready()
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
    
  