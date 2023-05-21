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
import sqlite3

# load variables from .env file
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
ZETPOOL_CHANNEL_ID = int(os.getenv('ZETPOOL_CHANNEL_ID'))

# create database directory
db_path = "data/db"
if not os.path.exists(db_path):
    os.makedirs(db_path)

# connect to database
conn = sqlite3.connect("data/db/ZET_ETCPool.db")
cur = conn.cursor() 

# create table for discord_users
cur.execute("""CREATE TABLE IF NOT EXISTS discord_users (
    user_id TEXT PRIMARY KEY, 
    wallet_number TEXT,
    payout_amount TEXT,
    payout_timestamp TEXT,
    payout_tx TEXT
    )""")

# commit the changes to the database
conn.commit()
    
# create table for workers with worker id as primary key and user id as foreign key   
cur.execute("""CREATE TABLE IF NOT EXISTS workers (
    wallet_number TEXT,
    worker_id TEXT, 
    offline BOOLEAN,
    PRIMARY KEY (wallet_number, worker_id),
    FOREIGN KEY (wallet_number) REFERENCES users (wallet_number)
    )""")    
    
# commit the changes to the database
conn.commit()

# close the connection
conn.close()
'''
author_id = "1071380251529187378"
wallet = "0x6030c8112e68396416e98f8eeaabfade426e472b"
'''

            

        
 
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
        self.watch_wallet_check.start()
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
        
        # connect to database
        conn = sqlite3.connect("data/db/ZET_ETCPool.db")
        cur = conn.cursor() 
        # insert author_ad and wallet to database, replace wqallet if already exists
        cur.execute("""INSERT OR REPLACE INTO discord_users (user_id, wallet_number, payout_amount, payout_timestamp, payout_tx) VALUES (?, ?, NULL, NULL, NULL)""", (author_id, wallet))
        # commit the changes to the database
        conn.commit()
        # close the connection
        conn.close()
        await ctx.channel.send(f"Watch_Wallet For {wallet} Active!", delete_after=60.0)
        
        try:
            # remove wallet and user from wallet_watch  
            self.cached_wallets.pop(author_id)
        except:
            pass
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
    async def watch_wallet_check(self):
        # fix for AttributeError("'NoneType' object has no attribute 'send'")
        await self.bot.wait_until_ready()
        # dirty fix for "local variable 'user' referenced before assignment"
        try: 
            # create instance of a class
            zet_etc = ZET_ETC()
            # loop through every user having watch_wallet active
            for cached_user in self.cached_wallets:
                # create user from cached_user string
                user = self.bot.get_user(int(cached_user))
                
                # get wallet info via api
                wallet_data = zet_etc.getAccountsData(self.cached_wallets[cached_user]['Wallet'])
                
                # get latest payment info
                latest_payments = wallet_data['payments'][0]
                # add new Payment entry if not present
                if not 'Payment' in self.cached_wallets[cached_user]:
                    self.cached_wallets[cached_user]['Payment'] = latest_payments
                # compare timestamps of cached and new payments     
                else:
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
                        # create user from cached_user string
                        user = self.bot.get_user(int(cached_user))
                        await user.send(embed = embed_message)
                    # cache current payment
                    self.cached_wallets[cached_user]['Payment'] = latest_payments
                    
                # get workers status info
                workers_status = wallet_data['workers']
                # add workers entry if not present
                if not 'Workers' in self.cached_wallets[cached_user]:
                    self.cached_wallets[cached_user]['Workers'] = workers_status
                # compare statuses of cached and new data
                else:
                    # create embed
                    send_embed = False
                    embed_message = discord.Embed(title = f"WORKER OFFLINE!", description = f"Some workers went offline", color = discord.Color.red(), url = f"https://etc.zet-tech.eu/#/account/{self.cached_wallets[cached_user]['Wallet']}")
                    # get the value of the "offline" key for each cached worker
                    for name, status in self.cached_wallets[cached_user]['Workers'].items():
                        # check if values are different from current call
                        if workers_status[name].get('offline') != status['offline']:
                            # if change was from online to offline
                            if workers_status[name].get('offline') == True:
                                embed_message.add_field(name = f"{name}", value = f"{status['offline']}", inline = False)
                                send_embed = True
                    if send_embed:
                        # send list to user via private message   
                        await user.send(embed = embed_message)
                # cache current workers status
                self.cached_wallets[cached_user]['Workers'] = workers_status
        except:
           pass
        
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
        
        #for guild in self.bot.guilds:
        #    for channel in guild.text_channels:
        
        # get correct channel
        channel = self.bot.get_channel(ZETPOOL_CHANNEL_ID)
        # send message to the channel when new block arrives
        if height > self.cached_block["height"]:
            # create embed
            embed_message = discord.Embed(title = f"NEW BLOCK!", description = f"For ETC ZETpool", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/block/{hash}/transactions")
            embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
            embed_message.add_field(name = "Hash:", value = f"{hash}", inline = False) 
            embed_message.add_field(name = "Height:", value = f"{height}", inline = True) 
            embed_message.add_field(name = "Orphan:", value = f"{orphan}", inline = True)
            embed_message.add_field(name = "Uncle:", value = f"{uncle}", inline = True)
            embed_message.add_field(name = "Reward:", value = f"{reward} ETC", inline = True)
            embed_message.add_field(name = "Variance:", value = f"{variance}%", inline = True)
            embed_message.set_footer(text = f"@{dt_object}") 
            # send it
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
    
  