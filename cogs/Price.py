import discord
from discord.ext import commands
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pathlib import Path


# load variables from .env file
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
CMC_API_KEY = os.getenv('CMC_API_KEY')


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
            

class Price(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # trigger when class is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Price.py is ready")
    
    # get coin price    
    @commands.command()
    async def price(self, ctx, arg, description = "get price of coins such as BTC, ETH, and so on"):
        cmc = CMC(CMC_API_KEY)
        price = round(cmc.getPrice(arg)[arg]['quote']['USD']['price'], 2)
        await ctx.channel.send(f" 1 {arg} costs {price} USD")
   
   
async def setup(bot):
    await bot.add_cog(Price(bot))