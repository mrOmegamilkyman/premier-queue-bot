import os
import asyncio
import discord
import statistics

from datetime import datetime
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Player, Match, standardize_role


# Discord Bot Startup
load_dotenv() # You need a .env file in your folder to get any secrets
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=intents)

# SQL Alchemy Startup
engine = create_engine('sqlite:///app/main.db')
SessionMaker = sessionmaker(bind=engine)
session = SessionMaker()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

    for guild in bot.guilds:
        print(f'Connected to the following guild:\n {guild.name}(id: {guild.id})')

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    
    bot.loop.create_task(check_queue_timeouts())


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')
    else:
        await ctx.send(f"{error}")


@bot.tree.command(name="hello", description="Sends a greeting message to the user")
async def hello(interaction: discord.Interaction):
    embed = discord.Embed(title='Error', description='Invalid region. Please choose from: NA, EUW, EUN', color=0xff0000)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="say", description="Repeats a message back to the user")
@app_commands.describe(thing_to_say = "What should I say?")
async def say(interaction: discord.Interaction, thing_to_say: str):
    await interaction.response.send_message(f"{interaction.user.name} said: '{thing_to_say}'")


# Have this function also assign the players role in the cord
@bot.tree.command(name='register', description="Registers a user with the bot")
@app_commands.describe(ign = "Your username or 'summoner name' in League of Legends", 
                        region = "'NA' or 'EUW' or 'EUN'", 
                        role1="'Top', 'Jng', 'Mid', 'ADC', 'Sup'", 
                        role2="'Top', 'Jng', 'Mid', 'ADC', 'Sup'" )
async def register(interaction: discord.Interaction, ign: str, region: str, role1:str, role2:str):
    # Check if the Discord or IGN is already in the database
    existing_player = session.query(Player).filter_by(ign=ign).first()
    existing_ign = session.query(Player).filter_by(discord_id=interaction.user.id).first()

    if region.upper() not in ['NA', 'EUW', 'EUN']:
        embed = discord.Embed(title='Error', description='Invalid region. Please choose from: NA, EUW, EUN', color=0xff0000)
        await interaction.response.send_message(embed=embed)

    elif existing_player:
        # IGN is already in the database
        embed = discord.Embed(title='Error', description=f'The IGN {ign} is already taken. If you feel this is a contact an administrator.', color=0xff0000)
        await interaction.response.send_message(embed=embed)

    elif existing_ign:
        # User already has a player profile in the database
        embed = discord.Embed(title='Error', description='You already have a player profile. If you need to update your IGN, please contact an administrator.', color=0xff0000)
        await interaction.response.send_message(embed=embed)

    else:
        # we need to fix the roles that players might input
        role1 = standardize_role(role1)
        role2 = standardize_role(role2)
        if role1 is None or role2 is None:
            await interaction.response.send_message("Sorry, the roles you entered were not recognized. Please enter one of the following roles: Top, Jgl, Mid, Adc, Sup")
            
        else:
            player = Player(discord_id=interaction.user.id, ign=ign, region=region, role1=role1, role2=role2)# We need to auth this somehow
            session.add(player)
            session.commit()
            print(f'Created a new player profile for {player}!')
            embed = discord.Embed(title='Success', description=f'Created a new player profile for {ign}!', color=0x00ff00)
            await interaction.response.send_message(embed=embed)



@bot.tree.command(name='roles', description="Updates roles for the user")
@app_commands.describe(role1="'Top', 'Jng', 'Mid', 'ADC', 'Sup'", role2="'Top', 'Jng', 'Mid', 'ADC', 'Sup'" )
async def roles(interaction: discord.Interaction, role1:str, role2:str):
    # Just allow the player to change their roles
    player = session.query(Player).filter_by(discord_id=interaction.user.id).first()

    # Convert the input to upper case to allow for case-insensitive matching
    role1 = standardize_role(role1.upper())
    role2 = standardize_role(role2.upper())
    
    if role1 is None or role2 is None:
        embed = discord.Embed(title='Error', description='Invalid role. Please choose from: Top, Jng, Mid, Bot, Sup', color=0xff0000)
        await interaction.response.send_message(embed=embed)
        return

    # Update the player's roles
    player.role1 = role1
    player.role2 = role2
    session.commit()
    embed = discord.Embed(title='Success', description=f'Updated {player.ign}\'s roles to {player.role1} and {player.role2}', color=0x00ff00)
    await interaction.response.send_message(embed=embed)


# This function needs to actually balance teams based on the elos of the players
# It should split the teams and balance the teams by minimizing the difference in the average ratings on each side
# It should also probably try to make the teams so the players get their primary/secondary role.
def balance_teams(queue_dict):
    # Sort the players by rating in descending order
    sorted_players = sorted(queue_dict.keys(), key=lambda x: x.rating, reverse=True)

    # Split the players into two lists
    half = len(sorted_players) // 2
    team_1 = sorted_players[:half]
    team_2 = sorted_players[half:]

    # Calculate the average ratings for each team
    avg_rating_1 = statistics.mean([player.rating for player in team_1])
    avg_rating_2 = statistics.mean([player.rating for player in team_2])

    # Check if the difference in average rating is greater than 100
    # If it is, swap the lowest rating player on team 1 with the highest rating player on team 2
    while abs(avg_rating_1 - avg_rating_2) > 100:
        low_player = min(team_1, key=lambda x: x.rating)
        high_player = max(team_2, key=lambda x: x.rating)
        team_1.remove(low_player)
        team_2.remove(high_player)
        team_1.append(high_player)
        team_2.append(low_player)

        # Recalculate the average ratings for each team
        avg_rating_1 = statistics.mean([player.rating for player in team_1])
        avg_rating_2 = statistics.mean([player.rating for player in team_2])

    return team_1, team_2


queue_dict = {} #(player:time)
match_id = 0
@bot.command(name='queue', aliases=['q'], help="Adds the user to a queue")
async def join_queue(ctx):
    global queue_dict
    global match_id
    player = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    
    if player is None:
        await ctx.send(f"Sorry no account was found for <@{ctx.author.id}>, are you sure you did `?register` ?")
    elif player in queue_dict:
        
        embed = discord.Embed(title=f"{player.ign} already in queue ({len(queue_dict)}/10)", color=0x944a94)            
        embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player, time in queue_dict.items()))
        await ctx.send(embed=embed)
    else:
        queue_dict[player] = datetime.now()
        embed = discord.Embed(title=f"{player.ign} has joined the queue ({len(queue_dict)}/10)", color=0x944a94)            
        embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player, time in queue_dict.items()))
        await ctx.send(embed=embed)

    # Match Find not sure if this code should be here or somewhere else
    if len(queue_dict) == 10:
        team_1, team_2 = balance_teams(queue_dict)
        roles = ["Top", "Jng", "Mid", "ADC", "Sup"]
        # Delete the queue list now that we have the teams
        queue_dict = {}

        blue_team_field = '\n'.join(f"{roles[i]} - {player.discord_id} μ: {player.rating}" for i, player in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} - {player.discord_id} μ: {player.rating}" for i, player in enumerate(team_2))

        # create a new match in the match table here and replace "match_id" with match.id

        embed = discord.Embed(title=f"Match #{match_id} starting ...", color=0x944a94)
        embed.add_field(name='Blue Team 🔵', value=blue_team_field, inline=True)
        embed.add_field(name='Red Team 🔴', value=red_team_field, inline=True)
        await ctx.send(embed=embed)

        embed = discord.Embed(title=f"⚠️After Match", description=f"Use `?win blue` or `?win red` to finish the match.", color=0xebcc34)
        await ctx.send(embed=embed)



@bot.command(name='leave', aliases=['l'], help='Removes the user from the queue')
async def leave_queue(ctx):
    global queue_dict
    # Auto leave queue after 10 min somehow
    player = session.query(Player).filter_by(discord_id=ctx.author.id).first()
    if player in queue_dict:
        del queue_dict[player]
        embed = discord.Embed(title=f"You have left the queue ({len(queue_dict)}/10)", color=0x944a94)
        if len(queue_dict) > 0:
            embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player, time in queue_dict.items()), inline=True)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=f"You are not in queue!", color=0x944a94)
        await ctx.send(embed=embed)


async def check_queue_timeouts():
    while True:
        purge_list = []
        for player, jointime in queue_dict.items():
            if (datetime.now() - jointime).total_seconds() > 300: # 300 seconds is 5 minutes
                purge_list.append(player)
                print(f"{player.ign} removed from queue!")
        
        for player in purge_list:
            del queue_dict[player]

        await asyncio.sleep(60) # check every 60 seconds


@bot.tree.command(name="win", description="Reports the result of a game")
@app_commands.describe(team = "Which team won the game? (blue or red)")
@commands.has_role("Manager")
async def win(interaction: discord.Interaction, team: str):
    global match_id
    user = session.query(Player).filter_by(discord_id=interaction.user.id).first()
    guild = bot.guilds[0]
    members = [f"{member.name} - μ: 1500" for member in guild.members]
    team_1 = members[:5]
    team_2 = members[5:10]
    roles = ["Top -", "Jgl -", "Mid -", "ADC -", "Sup -"]

    if team.lower() == "blue":
        embed = discord.Embed(title=f"Match #{match_id}: Blue Team 🔵 has won!", color=0x0000ff)
        blue_team_field = '\n'.join(f"{roles[i]} {member} **+15**" for i, member in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} {member} **-15**" for i, member in enumerate(team_2))

    elif team.lower() == "red":
        embed = discord.Embed(title=f"Match #{match_id}: Red Team 🔴 has won!", color=0xff0000)
        blue_team_field = '\n'.join(f"{roles[i]} {member} **-15**" for i, member in enumerate(team_1))
        red_team_field = '\n'.join(f"{roles[i]} {member} **+15**" for i, member in enumerate(team_2))

    embed.add_field(name='Blue Team 🔵', value=blue_team_field, inline=True)
    embed.add_field(name='Red Team 🔴', value=red_team_field, inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rating", description="Shows the user's rating")
@app_commands.describe(ign = "IGN of the player (optional, if not provided will check your own rating)")
async def check_rating(interaction: discord.Interaction, ign: str=None):

    if ign:
        user = session.query(Player).filter_by(ign=ign).first()
    else:
        user = session.query(Player).filter_by(discord_id=interaction.user.id).first()

    embed = discord.Embed(title=f"{user.ign}'s Rating", description=f'Rating: {user.rating} \nStandard Deviation: ±{user.deviation}', color=0x944a94)
    await interaction.response.send_message(embed=embed)



bot.run(TOKEN)