import os
import discord

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
bot = commands.Bot(command_prefix='/', intents=intents)

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


# This function needs to update the players roles in tha database
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


def balance_teams(members):
    team_1 = members[0:5]
    team_2 = members[5:10]
    return team_1, team_2


queue_list = []
match_id = 0
@bot.command(name='queue', help="Adds the user to a queue")
async def join_queue(ctx):
    global queue_list
    global match_id

    player = session.query(Player).filter_by(discord_id=ctx.author.id).first()

    if player is None:
        await ctx.send(f"Sorry no account was found for <@{ctx.author.id}>, are you sure you did `?register` ?")
    elif player in queue_list:
        embed = discord.Embed(title=f"{player.ign} already in queue ({len(queue_list)}/10)", color=0x944a94)            
        embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player in queue_list))
        await ctx.send(embed=embed)
    else:
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


@bot.tree.command(name='leave', description='Removes the user from the queue')
async def leave_queue(interaction: discord.Interaction):
    global queue_list
    # Auto leave queue after 10 min somehow
    player = session.query(Player).filter_by(discord_id=interaction.user.id).first()
    queue_list.remove(player)
    embed = discord.Embed(title=f"You have left the queue ({len(queue_list)}/10)", color=0x944a94)
    embed.add_field(name="Players: ", value='\n'.join(f"<@{player.discord_id}>" for player in queue_list))
    await interaction.response.send_message(embed=embed)


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