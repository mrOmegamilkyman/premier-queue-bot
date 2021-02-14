# bot.py
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from chegg_scraper import get_chegg_images

load_dotenv() # You need a .env file in your folder to get any secrets
TOKEN = os.getenv('DISCORD_TOKEN')
CHEGG_USER = os.getenv('CHEGG_USER')
CHEGG_PASSWORD = os.getenv('CHEGG_PASSWORD')

bot = commands.Bot(command_prefix='?')


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user} in server: {bot.guilds[0]}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

    
@bot.command(name='chegg', help="Fetches chegg answers for any given URL")
@commands.has_role("Business Men")
async def chegg(ctx, url: str=None):
    example_url = "https://www.chegg.com/homework-help/questions-and-answers/consider-circuit-\
    -use-node-voltage-method-obtain-node-voltages-v1-v2-v3-use-linsolve-funct-q55827065"

    if url == None:
        await ctx.send("Missing URL")
    elif url[0:58] == "https://www.chegg.com/homework-help/questions-and-answers/":
        # Need to implement get_chegg_images() function, In the meantime send test.png
        # images = get_chegg_images(url, user=CHEGG_USER, password=CHEGG_PASSWORD) 
        images = 'images/test.png'
        await ctx.send(file=discord.File(images))
    else:
        await ctx.send("Invalid URL.")


@chegg.error
async def chegg_error(ctx, error):
    await ctx.send(error)


@bot.command(name='py', help="Uses python's built in 'eval()' function and returns the result.")
@commands.has_role("Business Men")
async def py(ctx, *, code):
    #A bad example of an eval command
    await ctx.send(eval(code))

   

bot.run(TOKEN)

