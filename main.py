import discord
from discord.ext import commands, tasks

import os
from dotenv import load_dotenv
from pathlib import Path

import requests
import json

import random

import logging
import logging.handlers
import os

import asyncio

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from itertools import cycle

description = "Simple Discord Boot [WIP]"


class CMC:
    # https://coinmarketcap.com/api/documentation/v1/#
    def __init__(self, token):
        self.api_url = 'https://pro-api.coinmarketcap.com'
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
        }
        self.session = Session()
        self.session.headers.update(self.headers)
               
    def getPrice(self, symbol):
        url = self.api_url + '/v1/cryptocurrency/quotes/latest'
        parameters = {'symbol': symbol}
        try:
            r = self.session.get(url, params = parameters)
            data = r.json()['data']
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


# create directory to store logs
if not os.path.exists("logs"):
  os.makedirs("logs")

# setup logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='logs\discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# load variables from .env file
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
TOKEN = os.getenv('TOKEN')
CMC_API_KEY = os.getenv('CMC_API_KEY')

# enable message intent
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# connect to discord
bot = commands.Bot(command_prefix='!', description=description, intents=intents)

# sad words
sad_words = ["sad", "depressed", "mad", "unhapy", "heartbroken", "miserable", "upset", "hurt", "hurts"]

# bot status
bot_status = cycle(["type in !help", "for commands list"])



# trigger when bot ready to use
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print('------')
    change_status.start()

# load cogs from files    
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"{filename[:-3]} is loaded")

# display bot status
@tasks.loop(seconds=5)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(bot_status)))

# trigger when message received     
@bot.event
async def on_message(ctx):
    # don't respond to own messages
    if ctx.author.id == bot.user.id:
        return   
        
    # respond to sad words
    if any(word in ctx.content for word in sad_words):
        try:
            with open("./data/responses_to_sad_words.txt", "r") as f: 
                responses_to_sad_words = f.readlines()
                response = random.choice(responses_to_sad_words)
        except:
           response = "Cheer up!"
        await ctx.channel.send(response)
        
    # process bot commands
    await bot.process_commands(ctx)
    
# countdown from 3 to 0
@bot.command()
async def countdown(ctx, description = "countdown from 3 to 0"):
    msg = await ctx.send('3')
    await asyncio.sleep(1.0)
    await msg.edit(content='2')
    await asyncio.sleep(1.0)
    await msg.edit(content='1')
    await asyncio.sleep(1.0)
    await msg.edit(content='GO!')

# get coin price    
@bot.command()
async def price(ctx, arg, description = "get price of coins such as BTC, ETH, and so on"):
    cmc = CMC(CMC_API_KEY)
    price = round(cmc.getPrice(arg)[arg]['quote']['USD']['price'], 2)
    await ctx.channel.send(f" 1 {arg} costs {price} USD")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)
        
        
asyncio.run(main())
