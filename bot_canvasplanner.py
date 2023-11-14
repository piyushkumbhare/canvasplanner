"""####################################################################
IMPORT LIBRARIES
"""####################################################################

#Standard Libraries
import requests
import os
import datetime
import json
import asyncio
import math
import re

#Non-standard Libraries installed with pip
import discord
from discord import app_commands
from discord.utils import get
from discord.ext import commands, tasks

from dotenv import load_dotenv

import pytz

import datetime


"""####################################################################
GLOBAL VARIABLES
"""####################################################################

load_dotenv()

BOT_ID = int(os.getenv('BOT_ID'))
BOT_TOKEN = os.getenv('BOT_TOKEN')

MY_ID = int(os.getenv('MY_ID'))

CANVAS_TOKEN = os.getenv('CANVAS_TOKEN')

#Daily task run time
# PST = UTC - 8
run_time = datetime.time(hour=16, minute=00)


def on_command(interaction):
    if(interaction.guild is None):
        print(f"-- Direct Message with {interaction.user.name}: `/{interaction.command.name}` by {interaction.user.name}")
    else:
        print(f"-- {interaction.guild.name}({interaction.guild.id}): `/{interaction.command.name}` by {interaction.user.name}")

    return

def writeToFile():

    try:
        json_object = json.dumps(userInfo, indent=4)
    except Exception as e:
        print(f"\tCRITICAL ERROR: When trying to json.dumps(), ran into\n: {e}")
        return
    
    with open('users.json', 'w+') as j:
        j.write(json_object)
        print(f"\tWrote to file `users.json` successfully.")
    return


"""####################################################################
BOT INITIALIZATION
"""####################################################################

bot = commands.Bot(command_prefix='$', owner_id = MY_ID, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("-- Bot is starting up.")

    global userInfo
    with open('users.json', 'r') as f:
        userInfo = json.load(f)
        print(f"\tLoaded info for {len(userInfo)} users.")
    print(f"\tTime right now: {datetime.datetime.utcnow()}")
    print(f"\tDaily task will run once per day at {run_time} UTC")
    
    # daily_task.start()
    
    activity = discord.Activity(type=discord.ActivityType.listening, name="/help ✅")
    await bot.change_presence(activity=activity)

    return

        
@tasks.loop(time=run_time)
async def daily_task():
    await daily(ids=[])
        



"""####################################################################
DEV COMMANDS
"""####################################################################
@bot.command()
@commands.dm_only()
async def printjson(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$printjson` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    called_by_owner = await bot.is_owner(ctx.author)

    if called_by_owner == False:
        await ctx.send("Only the owner can call this command! Hands off!")
        return

    jsondict = json.dumps(userInfo, indent=4)

    await ctx.send(f"```{jsondict}```")
    return



@bot.command()
@commands.dm_only()
async def save_values(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$save_values` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    called_by_owner = await bot.is_owner(ctx.author)

    if called_by_owner == False:
        await ctx.send("Only the owner can call this command! Hands off!")
        return

    #If it is me calling it, write JSON files.
    writeToFile()
    
    await ctx.send("Values saved, boss. :saluting_face:")
    return

@bot.command()
@commands.dm_only()
async def sd(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$sd` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    called_by_owner = await bot.is_owner(ctx.author)
   
    # activity = discord.Activity(type=discord.ActivityType.streaming, name="Offline ⛔")
    # bot.change_presence(activity=activity)

    if called_by_owner == False:
        await ctx.send("Only the owner can call this command! Hands off!")
        return

    #If it is me calling it, write JSON files.
    writeToFile()

    await ctx.send("Shutting down. Until next time... :wave:")
    print()
    
    #Then close bot
    print("-- Bot Shutting Down")
    await bot.close()
    print()
    return


@bot.command()
@commands.dm_only()
async def sync(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$sync` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    if(await bot.is_owner(ctx.author) == False):
        await ctx.send("This command is for owners only. Hands off!")
        return
    
    count = await bot.tree.sync()
    print(f"\tSynced {len(count)} commands!")
    await ctx.send(f"Successfully synced {len(count)} commands!")
    return

@bot.command()
@commands.dm_only()
async def simdaily(ctx: commands.context.Context):
    if(await bot.is_owner(ctx.author) == False):
        await ctx.send("This command is for owners only. Hands off!")
        return
    print(f"-- Direct message with {ctx.author.name}: `$simdaily` called by {ctx.author.name}")

    args = ctx.message.content.split()
    ids = []
    for arg in args[1::]:
        for userid, userdata in userInfo.items():
            if(arg == userdata['name']):
                ids.append(userid)
    await daily(ids=ids)
    return



async def daily(ids=None):
    print("-- Starting Daily Task")

    me = bot.get_user(MY_ID)
    await me.send("Hello sir, just checking in. The daily tasks are under way. As you were.")   

    # First save to the file
    writeToFile()

    global userInfo
    users_to_iterate = ids if (len(ids) > 0) else list(userInfo.keys())

    await me.send([bot.get_user(int(i)).name for i in users_to_iterate])   
    print(f"\t{users_to_iterate}")

    for user_id in users_to_iterate:
        # If user has notifications toggled off, skip
        if(userInfo[user_id]['notifications'] == False):
            print(f"\tSkipping reminders for {userInfo[user_id]['name']}")
            continue
        print(f"\tSending reminders for {userInfo[user_id]['name']}")

        assignments = fetch_assignments(user_id=user_id)    
        incomplete_assignments = sum(len(l) for l in assignments.values())

        if(incomplete_assignments == 0):
            print(f"\t{bot.get_user(int(user_id)).name} has no pending assignments!")
            continue

        user = bot.get_user(int(user_id))
        user = bot.get_user(MY_ID)

        embed = create_assignment_embed(assignments=assignments, days=userInfo[user_id]['days-warning'])
        embed.set_footer(text="(To toggle notifications off, type `/toggle-notifications False`)")
        
        await user.send(embed=embed)

        print(f"\tSuccessfully sent reminders for {userInfo[user_id]['name']}")

    return



"""####################################################################
BOT COMMANDS
"""####################################################################

@bot.tree.command(name="help", description="Shows descriptions for all commands and how to use the bot.")
async def help_command(interaction: discord.Interaction):
    on_command(interaction)

    embed = discord.Embed(title='Need help? Look no further!', color=discord.Color.dark_blue(), )

    how_it_works = """
- This bot will send out a reminder DM every day at 7:00 AM (PST) **only** if you have assignments due.
- Assignments that are marked complete on Canvas will be automatically detected by this bot.
- However, if assignments are completed via 3rd-party websites (i.e Gradescope, Achieve, etc), this bot will not be able to detect completion.

"""
    embed.add_field(name="**__How does this bot work?__**", value=how_it_works, inline=False)

    embed.add_field(name="__**Below is a list of commands you can use with this bot!**__", value="\u200b", inline=False)

    setup_desc = """- Sets the API Token and Host URL for your Canvas account. Upon first use, you **must** include both arguments. *(They can each be updated later)*
- ❗**This command must be called before accessing any features of the bot.**"""
    embed.add_field(name="__`/setup-user`__", value=setup_desc, inline=False)
    
    toggle_desc = """- Toggles notifications on/off. You will be reminded of an asssignment if it is due in less than `<dayswarning>` days. 
- Default: `<toggle> = True`, `<dayswarning> = 1`."""
    embed.add_field(name="__`/toggle-notifications <toggle> <dayswarning>`__", value=toggle_desc, inline=False)

    get_assignments_desc = """- Returns the list of upcoming assignments from all Dashboard Courses due in `<days>` days (default 7 days)."""
    embed.add_field(name="__`/get-assignments`__", value=get_assignments_desc, inline=False)

    get_courses_desc = """- Returns a list of your Dashboard Courses
- For a course to appear on your Dashboard, it must be \"Favorited\" on Canvas. This is done for you by your school most of the time."""
    embed.add_field(name="__`/get-courses`__", value=get_courses_desc, inline=False)

    help_desc = """- Prints this message"""
    embed.add_field(name="__`/help`__", value=help_desc, inline=False)

    await interaction.response.send_message(embed=embed)
    return



class Setup(discord.ui.Modal, title='Let\'s get you set up!'):
    url = discord.ui.TextInput(label='Your Canvas Page URL', required=False, placeholder='canvas.example.edu')
    token = discord.ui.TextInput(label='Your Canvas API', style=discord.TextStyle.paragraph, placeholder='A long string found on your Canvas Settings page.', required=False)

    # button = discord.ui.Button(label="Submit", custom_id='confirm')

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()



@bot.tree.command(name="setup", description="Set the API Token and URL Instance for your user.")
# @app_commands.describe(token="Your Canvas API Token. This is a long string that can be obtained from your Canvas Profile Settings.", base_url="Where your Canvas account is hosted from (ie. `canvas.ucsc.edu`)")
async def setup_user(interaction: discord.Interaction):
    on_command(interaction)
    
    # DISABLED FOR NOW
    # This checks to make sure the command is called in a DM.
    # if(interaction.guild is not None):
    #     print(f"\tUser tried calling DM command in Guild.")
    #     await interaction.channel.send("You cannot call this command in a server! Please DM this command to me instead!\nI have deleted the original message, but I still recommend that you reset your API Token for safety")
    #     await interaction.response.send_message("Deleting interaction.")
    #     await interaction.delete_original_response()
    #     return

    modal = Setup()
    await interaction.response.send_modal(modal)

    errored = await modal.wait()

    print("View finished normally?", not errored)

    #If the view does not close properly (aka it times out or if the user presses Cancel/Esc), return and exit function.
    if(errored): return

    base_url = str(modal.url)
    token = str(modal.token)

    print(base_url, token)



    if(len(base_url) + len(token) == 0):
        await interaction.followup.send(f"""
You cannot call this command with no inputs!
Call with one or both of the following:

**API Token** - A long string found on your Canvas Settings page. Click `[+ New Access Token]` and copy paste!

**URL Instance** - The URL where your Canvas account is hosted. Copy paste any URL from your Canvas.        
        """)
        return

    # Stringify User's id to stay consistent with JSON dictionaries.
    user_id = str(interaction.user.id)

    # Check if the user exists in the userInfo dictionary.
    if(user_id not in userInfo.keys()):
        print(f"\tNew user detected ({user_id}). Adding to `userInfo` dictionary.")

        #The user must provide both arguments when first setting up.
        if(len(token) + len(base_url) == 0):
            print(f"\tUser did not provide both Token & BaseURL upon first calling. Failed.")
        
            await interaction.followup.send("Since this is your first time setting up on the Canvas Bot, you must provide both your API Token & URL Instance. These can be updated later if you wish.")
            return

    # These if statements grab the URL instance and/or Token if they were left blank. 
    # If either is None, that means they exist within the dictionary already. Both cannot be None due to the previous checks.
    
    if(len(base_url) == 0):
        base_url = userInfo[user_id]['canvas-instance']
    else:
        print(f"\tUser inputted: {base_url}")
        result = re.search(r"(\w+\.\w+\.\w+).*$", base_url)
        if result is None:
            print(f"\tError: Invalid URL")
            await interaction.followup.send(f"`{base_url}` is not a valid URL!", ephemeral=True)
            return
        base_url = result.group(1)
        print(f"\tExtracted group: {base_url}")


    if(len(token) == 0):
        token = userInfo[user_id]['canvas-token']

    failure = False
    # Make a GET request to Canvas to retrieve user's Name and ID.
    try:
        canvas_request = requests.get(f"https://{base_url}/api/v1/users/self?access_token={token}")
        failure = not validCode(canvas_request.status_code)
    except Exception as e:
        print(f"\tRan into Exception: [{e}] when performing GET request")
        failure = True

    # If failure, end and delete interaction
    if(failure):            
        print(f"\tError with Canvas GET request")

        await interaction.followup.send(f"There was a problem with the outgoing request to Canvas. Make sure your API Access Token is up to date and your URL Instance is correct.", ephemeral=True)
        return
    
    else:
        print(f"\tSuccessful Canvas GET request: Status Code {canvas_request.status_code}")

    # Get the JSON output of the response.
    canvas_json = canvas_request.json()

    # Update user info within the dictionary.
    userInfo[user_id] = {
        'name': interaction.user.name,
        'canvas-token': token,
        'canvas-instance': base_url,
        'canvas-name': canvas_json['name'],
        'canvas-id': canvas_json['id'],
        'notifications': True,
        'days-warning': 1,
        'pending-assignments': {},
        'completed-assignments': []
    }
        
    await interaction.followup.send("Your settings have been updated.")    
    return
    # Phew... That was one long function...
    
@bot.tree.command(name="toggle-notifications", description="Toggle assignment reminder notifications on/off with N days-warning")
@app_commands.describe(toggle="Notifications: True = On | False = Off, (Default: True)", dayswarning="I will remind you this many days before an assignment is due. (Default: 1 day)")
async def toggle_notifications(interaction: discord.Interaction, toggle: bool=True, dayswarning: int=1):
    on_command(interaction)

    user_id = str(interaction.user.id)

    if(user_id not in userInfo.keys()):
        print(f"\tUser {interaction.user.name} not found in database. Aborting.")
        await interaction.response.send_message("It looks like you have not been added to my database yet. Please do so by calling /setup-user.")
        return
    
    userInfo[user_id]['notifications'] = toggle

    # Days-warning cannot be less than 1
    if(dayswarning < 1):
        dayswarning = 1

    userInfo[user_id]['days-warning'] = dayswarning

    if(toggle == True):
        await interaction.response.send_message(f"You will now receive a reminder {dayswarning} day(s) before an assignment is due!")
    else:
        await interaction.response.send_message("You will no longer receive reminders about assignment due dates")

    print(f"\tToggled notifications for {interaction.user.name} to {toggle} and {dayswarning} days.")

    return    

# Fetches assignments for a given user and returns a dictionary of courses -> assignments
def fetch_assignments(user_id: int) -> dict:
    
    canvas_instance = userInfo[user_id]['canvas-instance']
    canvas_token = userInfo[user_id]['canvas-token']
    canvas_id = userInfo[user_id]['canvas-id']
    days = userInfo[user_id]['days-warning']

    courses_request = requests.get(f"https://{canvas_instance}/api/v1/users/self/favorites/courses?access_token={canvas_token}")

    if(not validCode(courses_request.status_code)):            
        print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping user {userInfo[user_id]['name']}({user_id})")
        return None
    
    courses_json = courses_request.json()

    assignments = {}

    for course in courses_json:
        id = course['id']
        params = {
            'include': ['submission'],
            'per_page': 500
            }
        course_assignments = requests.get(f"https://{canvas_instance}/api/v1/users/{canvas_id}/courses/{id}/assignments?access_token={canvas_token}", params=params)
        
        if(not validCode(course_assignments.status_code)):            
            print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping assignment {id}")
            continue


        course_assignments_json = course_assignments.json()
        assignments[course['name']] = []
        for asgn in course_assignments_json:

            if(asgn['due_at'] is None):
                continue

        
            time_until_due = datetime.datetime.strptime(asgn['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.utcnow()
            # print(f"\t{asgn['name']}\t\t\t{time_until_due}")

            if time_until_due > datetime.timedelta(days=0) and time_until_due <= datetime.timedelta(days=days):
                assignments[course['name']].append((asgn['name'], time_until_due, asgn['submission']['submitted_at'] != None, asgn['html_url']))
    
    return assignments


@bot.tree.command(name="get-assignments", description="Returns a list of your upcoming assignments.")
@app_commands.describe(days="Show assignments due within this many days (Default 7)")
async def get_assignments(interaction: discord.Interaction, days: int=7):
    on_command(interaction)
    
    user_id = str(interaction.user.id)
    global userInfo    
    
    await interaction.response.defer()

    assignments = fetch_assignments(user_id=user_id)

    if(assignments == None):
        interaction.response.send_message(f"Looks like there was a problem with the request. Please make sure your APIs have been set up correctly.\n(run `/help` for more info)")

    # print(assignments)

    incomplete_assignments = sum(len(l) for l in assignments.values())
    if(incomplete_assignments == 0):
        print(f"\t{bot.get_user(int(user_id)).name} has no pending assignments!")
        no_asgn = discord.Embed(title="Assignments", description=f"Congratulations @{interaction.user.name}, you have no upcoming assignments!", color= discord.Color.green())
        await interaction.followup.send(embed=no_asgn)
        return
    
    embed = create_assignment_embed(assignments=assignments, days=userInfo[user_id]['days-warning'])
    
    await interaction.followup.send(embed=embed)

    print(f"\tSuccessfully sent reminders for {userInfo[user_id]['name']}")

    return


def create_assignment_embed(assignments: dict, days: int) -> discord.Embed:
    
    embed = discord.Embed(title="Assignment Reminder", description=f"Hey! here is a list of assignments that are due in the next {days} days!", color=discord.Color.green())
    
    for course_name, asgns in assignments.items():
        if(len(asgns) > 0):
            full = False
            msg = ""
            for (name, due_in, submitted, link) in asgns:
                # submitted = True
                # print(name, due_in, submitted)
                emoji = "✅" if submitted else "⛔"
                if(not submitted):
                    embed.color = discord.Color.red()
                line = f"- {emoji} *{name}* \n    - Due in {'**' * (due_in < datetime.timedelta(days=3))}{due_in.days} days, {math.floor(due_in.seconds/3600)} hours, and {math.ceil(due_in.seconds%3600 / 60)} minutes{'**' * (due_in < datetime.timedelta(days=3))}\n  - Link: {link}\n"
                if(len(msg) + len(line) > 1024):
                    full = True
                    embed.add_field(name=course_name, value=msg)
                    msg = ""
                msg += line
            # print(msg)
            # print(len(msg))
            embed.add_field(name="\u200b" if full else course_name, value=msg, inline=False)
    
    return embed



@bot.tree.command(name="get-courses", description="Returns a list of your active courses.")
async def get_courses(interaction: discord.Interaction):
    on_command(interaction)

    user_id = str(interaction.user.id)

    if(user_id not in userInfo.keys()):
        await interaction.response.send_message("It looks like you have not been added to my database yet. Please do so by calling /setup-user.")
        return

    canvas_instance = userInfo[user_id]['canvas-instance']
    canvas_token = userInfo[user_id]['canvas-token']
    canvas_id = userInfo[user_id]['canvas-id']

    courses_request = requests.get(f"https://{canvas_instance}/api/v1/users/self/favorites/courses?access_token={canvas_token}")

    if(not validCode(courses_request.status_code)):            
        print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}")

        await interaction.response.send_message(f"There was a problem with the outgoing request to Canvas. Make sure your API Access Token is up to date and your URL Instance is correct.")
        return
    
    else:
        print(f"\tSuccessful Canvas GET request: Status Code {courses_request.status_code}")

    courses_json = courses_request.json()

    message = "Here is a list of your active courses.\n```\n"
    count = 1
    embed = discord.Embed(title="Courses", description="Here is a list of your active courses", color=discord.Color.green())
    for i in courses_json:
        value = f"https://{canvas_instance}/courses/{i['id']}"
        embed.add_field(name=f"{count}. {i['name']}", value=value, inline=False)
        message += f"{count}. {i['name']}\n"
        count += 1
    message += "```"
    await interaction.response.send_message(embed=embed)
    return


"""####################################################################
DRIVER CODE
"""####################################################################


# Returns True if status code is successfull (aka 2xx)
def validCode(status_code):
    return (status_code >= 200 and status_code < 300)

def main():
    bot.run(BOT_TOKEN)
    

if __name__ == '__main__':
    main()
