import discord

import os
from dotenv import load_dotenv
from pathlib import Path

import requests
import json

import random

import logging
import os

# create directory to store logs
if not os.path.exists("logs"):
  os.makedirs("logs")

# define log file name
handler = logging.FileHandler(filename='logs\discord.log', encoding='utf-8', mode='w')

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

# sad words
sad_words = ["sad", "depressed", "mad", "unhapy", "heartbroken", "miserable", "upset", "hurt", "hurts"]
response_to_sad_words = [
    "Cheer up!", 
    "You can do it!", 
    "There is no need to be sad"
]


def get_joke():
    response = requests.get("https://api.chucknorris.io/jokes/random", timeout = 3)
    try:  
        joke = json.loads(response.text)['value']
    except:
        joke = "Why was 6 afraid of 7? Because 7,8,9."
    return joke


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
        
    # respond to joke request
    if message.content.startswith("$joke"):
        joke = get_joke()
        await message.channel.send(joke)
    
    # cheer up sad person
    if any(word in message.content for word in sad_words):
        await message.channel.send(random.choice(response_to_sad_words))
 
 
client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)