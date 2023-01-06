import os
import discord

from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Player, Match


# Discord Bot Startup
load_dotenv() # You need a .env file in your folder to get any secrets
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='?', intents=intents)

# SQL Alchemy Startup
engine = create_engine('sqlite:///app/main.db')
SessionMaker = sessionmaker(bind=engine)
session = SessionMaker()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

    for guild in bot.guilds:
        print(f'Connected to the following guild:\n {guild.name}(id: {guild.id})')
    
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')
    else:
        await ctx.send(f"{error}")


@bot.command(name='hello', help='Says hello')
async def say_hello(ctx):
    print('hello command initiated')
    await ctx.send("Hello!")


@bot.command(name='create_profile', help='Initiates a players profile with their IGN and their region')
async def create_profile(ctx, ign: str, region: str):
    # Check if the IGN is already in the database
    existing_player = session.query(Player).filter_by(ign=ign).first()
    existing_ign = session.query(Player).filter_by(discord_id=ctx.author.id).first()

    if region.upper() not in ['NA', 'EUW', 'EUN']:
        embed = discord.Embed(title='Error', description='Invalid region. Please choose from: NA, EUW, EUN', color=0xff0000)
        await ctx.send(embed=embed)

    elif existing_player:
        # IGN is already in the database
        embed = discord.Embed(title='Error', description=f'The IGN {ign} is already taken. Please choose a different IG or contact an administrator.', color=0xff0000)
        await ctx.send(embed=embed)

    elif existing_ign:
        # User already has a player profile in the database
        embed = discord.Embed(title='Error', description='You already have a player profile. If you need to update your IGN, please contact an administrator.', color=0xff0000)
        await ctx.send(embed=embed)

    else:
        player = Player(discord_id=ctx.author.id, ign=ign, region=region)# We need to auth this somehow
        session.add(player)
        session.commit()
        print(f'Created a new player profile for {player}!')
        embed = discord.Embed(title='Success', description=f'Created a new player profile for {ign}!', color=0x00ff00)
        await ctx.send(embed=embed)


@bot.command(name='update_profile', help='Initiates a players profile with their IGN and their region')
@commands.has_role("Admin")
async def update_profile(ctx, disc_id: str):
    # Check if the IGN is already in the database
    disc_id = int(disc_id[2:-1])
    msg = f"input:({disc_id}) Discord:({ctx.author.id})"

    print(msg)
    await ctx.send(msg)
    await ctx.send(disc_id == ctx.author.id)
    return
    existing_player = session.query(Player).filter_by(ign=ign).first()
    existing_ign = session.query(Player).filter_by(discord_id=ctx.author.id).first()

    if region.upper() not in ['NA', 'EUW', 'EUN']:
        embed = discord.Embed(title='Error', description='Invalid region. Please choose from: NA, EUW, EUN', color=0xff0000)
        await ctx.send(embed=embed)

    elif existing_player:
        # IGN is already in the database
        embed = discord.Embed(title='Error', description=f'The IGN {ign} is already taken. Please choose a different IGN.', color=0xff0000)
        await ctx.send(embed=embed)

    elif existing_ign:
        # User already has a player profile in the database
        embed = discord.Embed(title='Error', description='You already have a player profile. If you need to update your IGN, please contact an administrator.', color=0xff0000)
        await ctx.send(embed=embed)

    else:
        player = Player(discord_id=ctx.author.id, ign=ign, region=region)# We need to auth this somehow
        session.add(player)
        session.commit()
        print(f'Created a new player profile for {player}!')
        embed = discord.Embed(title='Success', description=f'Created a new player profile for {ign}!', color=0x00ff00)
        await ctx.send(embed=embed)


@bot.command(name='rating', help='Checks the users elo rating')
async def check_rating(ctx, ign: str=None):

    if ign:
        user = session.query(Player).filter_by(ign=ign).first()
    else:
        user = session.query(Player).filter_by(discord_id=ctx.author.id).first()

    embed = discord.Embed(title=f"{user.ign}'s Rating", description=f'Games Played: 0 \nRating: {user.rating} \nStandard Deviation: ±{user.deviation}', color=0x944a94)
    await ctx.send(embed=embed)


queue_amount = 0
@bot.command(name='queue', aliases=['q'], help='Player joins the queue')
async def join_queue(ctx):
    global queue_amount
    queue_amount += 1
    user = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    embed = discord.Embed(title=f"{user.ign} has joined the queue ({queue_amount}/10)", color=0x944a94)
    await ctx.send(embed=embed)

@bot.command(name='leave', help='Player joins the queue')
async def join_queue(ctx):
    global queue_amount
    queue_amount -= 1
    user = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    embed = discord.Embed(title=f"{user.ign} has left the queue ({queue_amount}/10)", color=0x944a94)
    await ctx.send(embed=embed)



bot.run(TOKEN)