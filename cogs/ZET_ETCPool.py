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
import eth_utils

# load variables from .env file
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
ZETPOOL_CHANNEL_ID = int(os.getenv('ZETPOOL_CHANNEL_ID'))

# create database directory
db_path = "data/db"
if not os.path.exists(db_path):
    os.makedirs(db_path)

# connect to database
conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
cur = conn.cursor() 

# create table for discord_users
cur.execute("""CREATE TABLE IF NOT EXISTS discord_users (
    user_id TEXT PRIMARY KEY, 
    wallet_number TEXT,
    payout_amount TEXT,
    payout_timestamp TEXT,
    payout_tx TEXT
    )""")
    
# create table for workers with worker id as primary key and user id as foreign key   
cur.execute("""CREATE TABLE IF NOT EXISTS workers (
    wallet_number TEXT,
    worker_id TEXT, 
    offline BOOLEAN,
    PRIMARY KEY (wallet_number, worker_id),
    FOREIGN KEY (wallet_number) REFERENCES users (wallet_number)
    )""")    

# create table for last block   
cur.execute("""CREATE TABLE IF NOT EXISTS last_block (
    height TEXT PRIMARY KEY
    )""")    
    
# commit the changes to the database
conn.commit()

# close the connection
conn.close()
 
   
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
            return None
    
    
    # get json for account
    def getAccountsData(self, wallet):
        url = self.api_url + '/api/accounts/'+wallet
        try:
            r = self.session.get(url)
            data = r.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)   
            return None
    


class ZET_ETCPool(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.new_block_check.start()
        self.watch_wallet_check.start()
    
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("ZET_ETCPool.py is ready")

    
    # add wallet to wallet_watch   
    @commands.command() 
    async def add_watch_wallet(self, ctx, wallet, description = "add wallet to watch list to get notifications, usage example: !add_watch_wallet 0x6030c8112e68396416e98f8eeaabfade426e472b"):
        # get user id
        author_id = str(ctx.author.id)
        
        # validate wallet 
        if not eth_utils.is_address(wallet):
            await ctx.channel.send(f"Invalid ETC address: {wallet}")
            return
        
        # connect to database
        try:
            conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
            cur = conn.cursor() 
            # insert author_ad and wallet to database, replace wqallet if already exists
            cur.execute("""INSERT OR REPLACE INTO discord_users (user_id, wallet_number, payout_amount, payout_timestamp, payout_tx) VALUES (?, ?, NULL, NULL, NULL)""", (author_id, wallet))
            # commit the changes to the database
            conn.commit()
            # close the connection
            conn.close()
        except Exception as e:
            await ctx.channel.send(f"Database error: {e}")
            return
    
        await ctx.channel.send(f"Watch_Wallet Active!")
        uzer = self.bot.get_user(int(author_id))
        await uzer.send(f"Watch_Wallet For {wallet} Active!")
    
    # remove wallet from wallet_watch   
    @commands.command() 
    async def remove_watch_wallet(self, ctx, description = "remove wallet from watch list and stop getting notifications, usage example: !remove_watch_wallet"):
        # get user id
        author_id = str(ctx.author.id)
        
        # connect to database
        conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
        cur = conn.cursor() 
        cur.execute("""DELETE FROM discord_users WHERE user_id = ? AND EXISTS (SELECT 1 FROM discord_users WHERE user_id = ?)""", (author_id, author_id))
        # commit the changes to the database
        conn.commit()
        # close the connection
        conn.close()
        await ctx.channel.send(f"Watch_Wallet Deactivated!")
       
       
    # check watch_wallet status   
    @tasks.loop(seconds = 60)
    async def watch_wallet_check(self):
        # fix for AttributeError("'NoneType' object has no attribute 'send'")
        await self.bot.wait_until_ready()

        # create instance of a class
        zet_etc = ZET_ETC()
        
        # connect to database
        conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
        cur = conn.cursor() 
        # get everything from discord_users database
        cur.execute("""SELECT user_id, wallet_number, payout_amount, payout_timestamp, payout_tx FROM discord_users""")
        # create empty lists for data
        users_list = []
        wallets_list = []
        amounts_list = []
        timestamps_list = []
        txs_list = []
        # put data into lists
        for row in cur.fetchall():
            users_list.append(row[0])
            wallets_list.append(row[1])
            amounts_list.append(row[2])
            timestamps_list.append(row[3])
            txs_list.append(row[4])
        # close the connection
        conn.close() 
        
        # loop through every user and wallet in list
        for user, wallet, amount, timestamp, tx in zip(users_list, wallets_list, amounts_list, timestamps_list, txs_list):
            
            # get wallet info via api
            wallet_data = zet_etc.getAccountsData(wallet)
            if wallet_data != None:
                # get latest payment info
                latest_payment = wallet_data['payments'][0]
                # do nothing if no payment data in db 
                if (timestamp is None):
                    timestamp = 999999999999
                    uzer = self.bot.get_user(int(user))
                    await uzer.send("Starting to monitor for any payouts...")
                # if latest payment timestmp is newer than cached one     
                elif (int(latest_payment['timestamp']) > int(timestamp)): 
                    # inform user about new payout via private message
                    amount = latest_payment['amount'] / (10**9)
                    tx = latest_payment['tx']
                    timestamp = latest_payment['timestamp']
                    dt_object = datetime.fromtimestamp(timestamp)
                    embed_message = discord.Embed(title = f"NEW PAYMENT!", description = f"Wallet: {wallet}", color = discord.Color.green(), url = f"https://blockscout.com/etc/mainnet/tx/{tx}")
                    embed_message.set_thumbnail(url="https://s2.coinmarketcap.com/static/img/coins/64x64/1321.png")
                    embed_message.add_field(name = "TX:", value = f"{tx}", inline = False) 
                    embed_message.add_field(name = "Amount:", value = f"{amount} ETC", inline = True) 
                    embed_message.set_footer(text = f"@{dt_object}")
                    # create user from cached_user string
                    uzer = self.bot.get_user(int(user))
                    await uzer.send(embed = embed_message)
                 
                # save current current payment info to db
                # connect to database
                conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
                cur = conn.cursor() 
                # insert current data to database, replace if already exists
                cur.execute("""INSERT OR REPLACE INTO discord_users (user_id, wallet_number, payout_amount, payout_timestamp, payout_tx) VALUES (?, ?, ?, ?, ?)""", (user, wallet, str(latest_payment['amount']), str(latest_payment['timestamp']), latest_payment['tx']))
                # commit the changes to the database
                conn.commit()
                # close the connection
                conn.close() 
                
                # get workers status info
                workers_status = wallet_data['workers']
                
                # connect to database
                conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
                cur = conn.cursor() 
                # get workers info for current wallet from workers table
                cur.execute("""SELECT worker_id, offline FROM workers WHERE workers.wallet_number = ?""", (wallet,))
                # create empty lists for data
                workers_id_list = []
                offline_list = []
                # put data into lists
                for row in cur.fetchall():
                    workers_id_list.append(row[0])
                    offline_list.append(row[1])
                # close the connection
                conn.close() 
                
                # do nothing if no workers data in db 
                if len(workers_id_list) < 1:
                    uzer = self.bot.get_user(int(user))
                    await uzer.send("Starting to monitor for workers that recently went offline...")
                # compare statuses of cached and new data
                else:
                    # create embed
                    send_embed = False
                    embed_message = discord.Embed(title = f"WORKER OFFLINE!", description = f"Some workers went offline", color = discord.Color.red(), url = f"https://etc.zet-tech.eu/#/account/{wallet}")
                    # get the value of the "offline" key for each cached worker
                    for worker_id, offline in zip(workers_id_list, offline_list):
                        # check if values are different from current call, use deafult worker_id in case it no longer exists
                        if workers_status.get(worker_id, {}).get('offline') != offline:
                            # if change was from online to offline, use deafult worker_id in case it no longer exists
                            if workers_status.get(worker_id, {}).get('offline') == True:
                                embed_message.add_field(name = f"{worker_id}", value = f"{offline}", inline = False)
                                send_embed = True
                    if send_embed:
                        # send list to user via private message
                        uzer = self.bot.get_user(int(user))                    
                        await uzer.send(embed = embed_message)
                        
                # connect to database
                conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
                cur = conn.cursor() 
                # save current workers info to db
                for name in workers_status.items():
                    cur.execute("""INSERT OR REPLACE INTO workers (wallet_number, worker_id, offline) VALUES (?, ?, ?)""", (wallet, str(name[0]), workers_status[name[0]].get('offline')))
                # commit the changes to the database
                conn.commit()
                # close the connection
                conn.close() 

        
    # check for new block    
    @tasks.loop(seconds = 60)
    async def new_block_check(self):
        await self.bot.wait_until_ready()
        
        # get cached height  from database
        # connect to database
        conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
        cur = conn.cursor() 
        # get height from last_block table
        cur.execute("SELECT height FROM last_block")
        result = cur.fetchone()
        # close the connection
        conn.close() 
        
        # check if result is not empty
        cached_height = 0
        if result is None:
            # create dummy block height 
            cached_height = 999999999999
        else:
            cached_height = int(result[0])

        # get block info via api
        zet_etc = ZET_ETC()
        pool_blocks_data = zet_etc.getBlocksData()
        if pool_blocks_data != None:
            latest_matured = pool_blocks_data['matured'][0]
            hash = latest_matured['hash']
            height = latest_matured['height']
            orphan = latest_matured['orphan']
            uncle = latest_matured['uncle']
            reward = latest_matured['reward'] / (10**9)
            variance = int(round(latest_matured['variance'] * 100))
            timestamp = latest_matured['timestamp']
            dt_object = datetime.fromtimestamp(timestamp)
        
            # get correct channel
            channel = self.bot.get_channel(ZETPOOL_CHANNEL_ID)
            # send message to the channel when new block arrives
            if int(height) > int(cached_height):
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
                        
            # save block height info to db
            # connect to database
            conn = sqlite3.connect("data/db/ZET_ETCPool.db", timeout = 30.0)
            cur = conn.cursor() 
            # insert current data to database, replace if already exists
            cur.execute("""REPLACE INTO last_block (height) VALUES (?)""", (str(height),))
            # commit the changes to the database
            conn.commit()
            # close the connection
            conn.close()        

      
    # get block info    
    @commands.command()
    async def block(self, ctx, description = "get info about latest ETC block mined by pool, usage example: !block"):
        
        zet_etc = ZET_ETC()
        pool_blocks_data = zet_etc.getBlocksData()
        if pool_blocks_data != None:
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
            
            await ctx.channel.send(embed = embed_message)

    
    # get payment info    
    @commands.command(aliases=["payout"])
    async def payment(self, ctx, wallet: str, description = "get info about latest payout to given ETC wallet, usage example: !payment 0x6030c8112e68396416e98f8eeaabfade426e472b"):
        
        zet_etc = ZET_ETC()
        wallet_payments_data = zet_etc.getAccountsData(wallet)
        if wallet_payments_data != None:
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
            
            await ctx.channel.send(embed = embed_message)

        



async def setup(bot):
    await bot.add_cog(ZET_ETCPool(bot))
    
  