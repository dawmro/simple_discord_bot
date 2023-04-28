import discord
from discord.ext import commands

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

description = "Simpe Discord Boot [WIP]"

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

# enable message intent
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# connect to discord
bot = commands.Bot(command_prefix='!', description=description, intents=intents)

# sad words
sad_words = ["sad", "depressed", "mad", "unhapy", "heartbroken", "miserable", "upset", "hurt", "hurts"]


def get_joke():
    response = requests.get("https://api.chucknorris.io/jokes/random", timeout = 3)
    try:  
        joke = json.loads(response.text)['value']
    except:
        joke = "Why was 6 afraid of 7? Because 7,8,9."
    return joke


# trigger when bot ready to use
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print('------')

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
    
# say hello
@bot.command()
async def hello(ctx, *args):
    await ctx.send(f"Hello {ctx.author}")

# tell joke
@bot.command()
async def joke(ctx, *args):
    joke = get_joke()
    await ctx.send(joke)
    
# delete message
@bot.command()
async def deleteme(ctx, *args):
    await ctx.send('I will delete myself in 3 seconds...', delete_after=3.0)
    
# countdown from 3 to 0
@bot.command()
async def countdown(ctx, *args):
    msg = await ctx.send('3')
    await asyncio.sleep(1.0)
    await msg.edit(content='2')
    await asyncio.sleep(1.0)
    await msg.edit(content='1')
    await asyncio.sleep(1.0)
    await msg.edit(content='GO!')


bot.run(TOKEN, log_handler=None)