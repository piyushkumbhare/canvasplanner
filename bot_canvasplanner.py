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
    daily.start()
    activity = discord.Activity(type=discord.ActivityType.listening, name="/help ✅")
    await bot.change_presence(activity=activity)

    return

        
@tasks.loop(time=run_time)
async def daily():
    await simulate_daily()
        



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

    await simulate_daily(ids=ids)
    return



async def simulate_daily(ids=None):
    print("-- Starting Daily Task")

    me = bot.get_user(MY_ID)
    await me.send("Hello sir, just checking in. The daily tasks are under way. As you were.")   

    # First save to the file
    writeToFile()

    global userInfo
    users_to_iterate = ids if (len(ids) > 0) else list(userInfo.keys())

    print(f"\t{users_to_iterate}")

    for user_id in users_to_iterate:
        # If user has notifications toggled off, skip
        if(userInfo[user_id]['notifications'] == False):
            print(f"\tSkipping reminders for {userInfo[user_id]['name']}")
            continue
        print(f"\tSending reminders for {userInfo[user_id]['name']}")
        

        canvas_instance = userInfo[user_id]['canvas-instance']
        canvas_token = userInfo[user_id]['canvas-token']
        canvas_id = userInfo[user_id]['canvas-id']

        courses_request = requests.get(f"https://{canvas_instance}/api/v1/users/self/favorites/courses?access_token={canvas_token}")

        if(not validCode(courses_request.status_code)):            
            print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping user {userInfo[user_id]['name']}({user_id})")

            continue
        
        courses_json = courses_request.json()

        # 'pending-assignments' is a dictionary mapping message ID -> assignment ID. For each message, check if it has a checkmark reaction.
        # If it does, then add it to the list of assignments to ignore.


        for message_id in userInfo[user_id]['pending-assignments'].keys():
            message = await bot.get_user(int(user_id)).fetch_message(int(message_id))
            for reaction in message.reactions:
                if reaction.count == 2:
                    print(f"\tReaction found on message {message_id}.")
                    completed = userInfo[user_id]['pending-assignments'][message_id]
                    userInfo[user_id]['completed-assignments'].append(completed)
        
        userInfo[user_id]['pending-assignments'] = {}
        
        assignments = []
        for course in courses_json:
            id = course['id']
            course_assignments = requests.get(f"https://{canvas_instance}/api/v1/users/{canvas_id}/courses/{id}/assignments?access_token={canvas_token}")
            
            if(not validCode(course_assignments.status_code)):            
                print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping assignment {id}")
                continue


            course_assignments_json = course_assignments.json()
            for asgn in course_assignments_json:

                if(asgn['due_at'] is None):
                    continue

                time_until_due = datetime.datetime.strptime(asgn['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.utcnow()
                one_day = datetime.timedelta(days=userInfo[user_id]['days-warning'])
                if time_until_due <= one_day and time_until_due > datetime.timedelta(days=0) and asgn['id'] not in userInfo[user_id]['completed-assignments']:
                    assignments.append((asgn, time_until_due, course['name']))

        if(len(assignments) > 0):    
            line = "----------------------------------------------------------------------\n"
            user = bot.get_user(int(user_id))


            await user.send(f"**REMINDER!**\nHey {userInfo[user_id]['canvas-name']}, here is a list of assignments that are due in the next {userInfo[user_id]['days-warning']} days!\nTo mark an assignment as complete, react to it with a :white_check_mark: \n*(To toggle notifications off, type `/toggle-notifications False`)*")
            
            for asgn, due_in, course_name in assignments:
                msg = f"{line}*{asgn['name']}* (Course: *{course_name}*)\nDue in: **{due_in.days} days, {math.floor(due_in.seconds/3600)} hours, and {math.ceil(due_in.seconds%3600 / 60)} minutes**\nHere is the link to the assignment: {asgn['html_url']}\n{line}"
                print(msg)
                
                message = await user.send(msg)

                await message.add_reaction("✅")

                userInfo[user_id]['pending-assignments'][message.id] = asgn['id']
                

            print(f"\tSuccessfully sent reminders for {userInfo[user_id]['name']}")
        else:
            print(f"\tUser {userInfo[user_id]['name']} has no assignments due. Woohoo!")

        return



"""####################################################################
BOT COMMANDS
"""####################################################################

@bot.tree.command(name="help", description="Shows descriptions for all commands and how to use the bot.")
async def help_command(interaction: discord.Interaction):
    on_command(interaction)

    message = """------------------------------------------------------------
How to use the bot:

- `/setup-user <API-Token> <URL-Instance>` - Sets the API Token and Host URL for your Canvas account. Upon first use, you **must** include both arguments. *(They can each be updated later)*

*API-Token* - A long string found on your Desktop Browser Canvas Settings page. Click `Account > Settings > + New Access Token and copy paste. But, once you create it, you cannot view it again unless you reset it, so be sure to copy paste!

*URL-Instance* - This is the site that hosts your Canvas Account. It is usually a school site, something like https://canvas.ucsc.edu/. To input, just copy and paste any URL from your canvas site.

**This command must be called before accessing any features of the bot. It also MUST be called in a DM with the bot. Never share your API Tokens!**


- `/toggle-notifications <toggle> <dayswarning>` - Toggles notifications on/off. You will be reminded of an asssignment if it is due in less than `<dayswarning>` days. 
Default: `<toggle> = True`, `<dayswarning> = 1`.

The bot will send out messages every day at 7:00 AM (PST) **only** if you have assignments due. You can mark an assignment as completed by reacting with a :white_check_mark: on it.
This reaction will be registered right before the next reminder is sent.


- `/get-assignments` - Returns the list of upcoming assignments from all Dashboard Courses.

- `/get-courses` - This command returns the list of your Dashboard Courses.

(For a course to show up on your Dashboard, it must be "Favorited" on Canvas. This is done for you by your school most of the time.)


- `/reset-completed-assignments` - Resets completed assignments. Only call if you accidentally marked an assignment as complete.
------------------------------------------------------------"""


    await interaction.response.send_message(message)
    return

@bot.tree.command(name="setup-user", description="Set the API Token and URL Instance for your user.")
@app_commands.describe(token="Your Canvas API Token. This is a long string that can be obtained from your Canvas Profile Settings.", base_url="Where your Canvas account is hosted from (ie. `canvas.ucsc.edu`)")
async def setup_user(interaction: discord.Interaction, token: str=None, base_url: str=None):
    on_command(interaction)
    
    # This checks to make sure the command is called in a DM.
    if(interaction.guild is not None):
        print(f"\tUser tried calling DM command in Guild.")
        await interaction.channel.send("You cannot call this command in a server! Please DM this command to me instead!\nI have deleted the original message, but I still recommend that you reset your API Token for safety")
        await interaction.response.send_message("Deleting interaction.")
        await interaction.delete_original_response()
        return

    if(base_url is None and token is None):
        await interaction.response.send_message(f"""
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
        if(token is None or base_url is None):
            print(f"\tUser did not provide both Token & BaseURL upon first calling. Failed.")
        
            await interaction.response.send_message("Since this is your first time setting up on the Canvas Bot, you must provide both your API Token & URL Instance. These can be updated later if you wish.")
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            return

    # These if statements grab the URL instance and/or Token if they were left blank. 
    # If either is None, that means they exist within the dictionary already. Both cannot be None due to the previous checks.
    
    if(base_url is None):
        base_url = userInfo[user_id]['canvas-instance']
    else:
        print(f"\tUser inputted: {base_url}")
        result = re.search(r"(\w+\.\w+\.\w+).*$", base_url)
        if result is None:
            print(f"\tError: Invalid URL")
            await interaction.channel.send(f"`{base_url}` is not a valid URL! It should include `canvas.xxxxx.xxx`")
            await interaction.response.send_message(f"Error. For your safety, this interaction will be deleted in 3 seconds.")
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            return
        base_url = result.group(1)
        print(f"\tExtracted group: {base_url}")


    if(token is None):
        token = userInfo[user_id]['canvas-token']

    failure = False
    # Make a GET request to Canvas to retrieve user's Name and ID.
    try:
        canvas_request = requests.get(f"https://{base_url}/api/v1/users/self?access_token={token}")
    except Exception as e:
        print(f"\tRan into Exception: [{e}] when performing GET request")
        failure = True

    # If failure, end and delete interaction
    if(not validCode(canvas_request.status_code) or failure == True):            
        print(f"\tError with Canvas GET request: Status Code {canvas_request.status_code} for:\n{canvas_request.url}")

        await interaction.response.send_message(f"There was a problem with the outgoing request to Canvas. Make sure your API Access Token is up to date and your URL Instance is correct.")
        await asyncio.sleep(3)
        await interaction.delete_original_response()    
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
        
    await interaction.response.send_message("Your settings have been updated. For your security, this interaction will be deleted in 3 seconds.")
    
    
    await asyncio.sleep(3)
    await interaction.delete_original_response()
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



@bot.tree.command(name="get-assignments", description="Returns a list of your upcoming assignments.")
async def get_assignments(interaction: discord.Interaction):
    on_command(interaction)

    user_id = str(interaction.user.id)

    if(user_id not in userInfo.keys()):
        print(f"\tUser {interaction.user.name} not found in database. Aborting.")
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

    await interaction.response.defer()
    courses_json = courses_request.json()

    assignments = []
    for i in courses_json:
        id = i['id']
        course_assignments = requests.get(f"https://{canvas_instance}/api/v1/users/{canvas_id}/courses/{id}/assignments?access_token={canvas_token}")
        
        course_assignments_json = course_assignments.json()
        assignments.extend(course_assignments_json)


    dateless_assignments = []

    to_remove = []

    for i in assignments:
        if(str(i['due_at']) == "None"):
            dateless_assignments.append(i)
            to_remove.append(i)
            # print(f"Assignment: {i['name']}, Due at: {i['due_at']}")

    for i in to_remove:
        assignments.remove(i)

    assignments = sorted(assignments, key=(lambda asgn : asgn['due_at']))    
    to_print = list(f"{i['name']:<60} Due in: {datetime.datetime.strptime(i['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.utcnow()}" for i in assignments if (datetime.datetime.strptime(i['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.today()) > datetime.timedelta(days=0))
    message = f"```{'Assignment Name': <60} Time until due\n"
    for i in to_print:
        message += i + '\n'

    message += '\nThe following assignments have no due date:\n'

    for i in dateless_assignments:
        message += f"{i['name']:<60}\n"


    message += '```'
    
    await interaction.followup.send(content=message)
    return



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
    for i in courses_json:
        message += f"{count}. {i['name']}\n"
        count += 1
    message += "```"
    await interaction.response.send_message(message)
    return


@bot.tree.command(name="reset-completed-assignments", description="Resets completed assignments. Only call this if you accidentally marked an assignment as complete.")
async def reset_completed_assignments(interaction: discord.Interaction):
    on_command(interaction)

    user_id = str(interaction.user.id)

    if(user_id not in userInfo.keys()):
        await interaction.response.send_message("It looks like you have not been added to my database yet. Please do so by calling /setup-user.")
        return   

    print(f"\tResetting [{userInfo[user_id]['completed-assignments']}] to [] (Empty List)")

    userInfo[user_id]['completed-assignments'] = [] 

    await interaction.response.send_message(f"Your completed assignments list has been reset.")

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
