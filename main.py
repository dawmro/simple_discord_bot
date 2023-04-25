import discord

import os
from dotenv import load_dotenv
from pathlib import Path

import requests
import json

import random

# load variables from .env file
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
TOKEN = os.getenv('TOKEN')

# enable message intent
intent = discord.Intents.default()
intent.members = True
intent.message_content = True

# connect to discord
client = discord.Client(intents=intent)

# trigger when bot ready to use
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


# trigger when message received 
@client.event
async def on_message(message):
    # don't respond to own messages
    if message.author == client.user:
        return
    
    # respond to hello message
    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")
 
 
client.run(TOKEN)