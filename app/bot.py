import os
import discord

from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Player, Match, standardize_role


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


@bot.command(name='register', help='Initiates a players profile with their IGN and their region')
async def register(ctx, ign: str, region: str, role1:str, role2:str):
    # Check if the Discord or IGN is already in the database
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
        # we need to fix the roles that players might input
        role1 = standardize_role(role1)
        role2 = standardize_role(role2)
        if role1 is None or role2 is None:
            await ctx.send("Sorry, the roles you entered were not recognized. Please enter one of the following roles: Top, Jgl, Mid, Adc, Sup")
            
        else:
            player = Player(discord_id=ctx.author.id, ign=ign, region=region, role1=role1, role2=role2)# We need to auth this somehow
            session.add(player)
            session.commit()
            print(f'Created a new player profile for {player}!')
            embed = discord.Embed(title='Success', description=f'Created a new player profile for {ign}!', color=0x00ff00)
            await ctx.send(embed=embed)

# This function needs worked on later
@bot.command(name='update_profile', help='Initiates a players profile with their IGN and their region')
@commands.has_role("Admin")
async def update_profile(ctx, disc_id: str):
    # Check if the IGN is already in the database
    disc_id = int(disc_id[2:-1])
    msg = f"input:({disc_id}) Discord:({ctx.author.id})"

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


def balance_teams(members):
    team_1 = members[0:5]
    team_2 = members[5:10]
    return team_1, team2


queue_list = []
match_id = 0
@bot.command(name='queue', aliases=['q'], help='Player joins the queue')
async def join_queue(ctx):
    global queue_list
    global match_id

    player = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    if player is None:
        await ctx.send(f"Sorry no account was found for <@{player.discord_id}>, are you sure you did `?register` ?")
    else:
        # Prob need to make sure player isnt already in the queue
        queue_list.append(player)
        embed = discord.Embed(title=f"{player.ign} has joined the queue ({len(queue_list)}/10)", color=0x944a94)            
        embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player in queue_list))
        await ctx.send(embed=embed)

    # Match Find
    if len(queue_list) == 10:
        team_1, team_2 = balance_teams(queue_list)
        roles = ["Top", "Jng", "Mid", "ADC", "Sup"]
        # Delete the queue list now that we have the teams
        queue_list = []

        blue_team_field = '\n'.join(f"{roles[i]} - {player.discord_id} μ: {player.rating}" for i, player in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} - {player.discord_id} μ: {player.rating}" for i, player in enumerate(team_2))

        # create a new match in the match table here and replace "match_id" with match.id
        embed = discord.Embed(title=f"Match #{match_id} starting ...", color=0x944a94)
        embed.add_field(name='Blue Team 🔵', value=blue_team_field, inline=True)
        embed.add_field(name='Red Team 🔴', value=red_team_field, inline=True)
        await ctx.send(embed=embed)

        embed = discord.Embed(title=f"⚠️After Match", description=f"Use `?win blue` or `?win red` to finish the match.", color=0xebcc34)
        await ctx.send(embed=embed)


@bot.command(name='leave', aliases=['l'], help='Player leaves the queue')
async def leave_queue(ctx):
    global queue_list
    queue_list.remove(ctx.author.id)
    embed = discord.Embed(title=f"You have left the queue ({len(queue_list)}/10)", color=0x944a94)
    embed.add_field(name="Players: ", value='\n'.join(f"<@{player}>" for player in queue_list))
    await ctx.send(embed=embed)


@bot.command(name='win', help='Command to tell bot which team won the game') # This can probably be automated by pulling the riot API with the players we know are in the game
@commands.has_role("Manager")
async def win(ctx, team: str):    
    global match_id
    user = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    guild = bot.guilds[0]
    members = [f"{member.name} - μ: 1500" for member in guild.members]
    team_1 = members[:5]
    team_2 = members[5:10]
    roles = ["Top -", "Jgl -", "Mid -", "ADC -", "Sup -"]

    if team == "blue":
        embed = discord.Embed(title=f"Match #{match_id}: Blue Team 🔵 has won!", color=0x0000ff)
        blue_team_field = '\n'.join(f"{roles[i]} {member} **+15**" for i, member in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} {member} **-15**" for i, member in enumerate(team_2))

    elif team == "red":
        embed = discord.Embed(title=f"Match #{match_id}: Red Team 🔴 has won!", color=0xff0000)
        blue_team_field = '\n'.join(f"{roles[i]} {member} **-15**" for i, member in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} {member} **+15**" for i, member in enumerate(team_2))

    embed.add_field(name='Blue Team 🔵', value=blue_team_field, inline=True)
    embed.add_field(name='Red Team 🔴', value=red_team_field, inline=True)

    await ctx.send(embed=embed)


@bot.command(name='rating', help='Checks the users elo rating')
async def check_rating(ctx, ign: str=None):

    if ign:
        user = session.query(Player).filter_by(ign=ign).first()
    else:
        user = session.query(Player).filter_by(discord_id=ctx.author.id).first()

    embed = discord.Embed(title=f"{user.ign}'s Rating", description=f'Games Played: 0 \nRating: {user.rating} \nStandard Deviation: ±{user.deviation}', color=0x944a94)
    await ctx.send(embed=embed)



bot.run(TOKEN)