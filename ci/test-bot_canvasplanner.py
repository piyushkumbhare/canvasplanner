"""####################################################################
IMPORT LIBRARIES
"""####################################################################

# Standard Libraries
import requests
import os
import datetime
import re
import sqlite3
import datetime

# Non-standard Libraries installed with pip
import discord
from discord import app_commands
from discord.utils import get
from discord.ext import commands, tasks

from dotenv import load_dotenv

# Local Libraries that contain utility functions
from canvas_tools import *

"""####################################################################
GLOBAL VARIABLES
"""####################################################################

load_dotenv()

con = sqlite3.connect("users.db")
cursor = con.cursor()
cursor.row_factory = sqlite3.Row

# users table is formatted as follows
# id    name    canvas_token    canvas_instance     canvas_name canvas_id   notifications   days_warning
# id = discord id
# name = discord name
# notifications = 0 | 1

# assignments table is formattes as follows
# id    owner   assignment_name assignment_id       course_name course_id   due_date        submitted   url
# INT   STR     STR             INT                 STR         INT         DATETIME        INT         STR

# due_date = YYYY-MM-DD HH:MI:SS

BOT_ID = int(os.getenv('BOT_ID'))
BOT_TOKEN = os.getenv('BOT_TOKEN')

MY_ID = int(os.getenv('MY_ID'))

CANVAS_TOKEN = os.getenv('CANVAS_TOKEN')

#Daily task run time
# PST = UTC - 8
run_time = datetime.time(hour=16, minute=00)

"""####################################################################
BOT INITIALIZATION
"""####################################################################

bot = commands.Bot(command_prefix='$', owner_id = MY_ID, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("-- Bot is starting up.")
    
    #Load SQL database
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print("Loading users...")
    for user in users:
        print(user['name'])
    print("Loading done.")

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
async def printdb(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$printdb` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    called_by_owner = await bot.is_owner(ctx.author)

    if called_by_owner == False:
        await ctx.send("Only the owner can call this command! Hands off!")
        return

    cursor.execute("SELECT * FROM users")
    users_rows = cursor.fetchall()

    users_row_str = ""
    for row in users_rows:
        users_row_str += str(dict(row)) + '\n'

    cursor.execute("SELECT * FROM assignments")
    assignments_rows = cursor.fetchall()

    assignments_row_str = ""
    for row in assignments_rows:
        assignments_row_str += str(dict(row)) + '\n'


    message = f"""## Users:
```
{users_rows[0].keys()}
{users_row_str}
```"""
# ## Assignments
# ```
# {assignments_rows[0].keys()}
# {assignments_row_str}
# ```

    await ctx.send(message)
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

    
    await ctx.send("Values saved, boss. :saluting_face:")
    return

@bot.command()
@commands.dm_only()
async def sd(ctx):
    print(f"-- Direct message with {ctx.author.name}: `$sd` called by {ctx.author.name}")
    #Check to see if it was called by owner.    
    called_by_owner = await bot.is_owner(ctx.author)
   

    if called_by_owner == False:
        await ctx.send("Only the owner can call this command! Hands off!")
        return

    await ctx.send("Shutting down. Until next time... :wave:")
    print()
    
    #Then close bot
    print("-- Bot Shutting Down")
    cursor.close()
    con.close()
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
    for name in args[1::]:
        
        cursor.execute(f"SELECT id FROM users WHERE name = '{name}'")
        user = cursor.fetchone()
        
        # if the name given was not found in database
        if(user is None):
            continue

        # if the name is found, return the id associated with it
        ids.append(user['id'])


    await daily(ids=ids)
    return



async def daily(ids):
    print("-- Starting Daily Task")

    me = bot.get_user(MY_ID)
    await me.send("Hello sir, just checking in. The daily tasks are under way. As you were.")   

    # First save to the file
    # writeToFile()

    users_to_iterate = []

    if(len(ids) > 0):

        # ok so this whole thing is here because SQL's IN statements have to be formatted like
        # SELECT ... WHERE id IN (1, 2, 3, 4);
        # so this idset thing is just the ids set, except expressed as a neat string with ()
        idset = "("
        for i in ids:
            idset += str(i) + "," * (i != ids[-1])
        idset += ")"
        
        
        q = f"SELECT * FROM users WHERE id IN {idset}"
        print(idset)
        print(f'\t{q}')
        cursor.execute(q)
        users_to_iterate = cursor.fetchall()
    else:
        cursor.execute(f"SELECT * FROM users")
        users_to_iterate = cursor.fetchall()

    await me.send([user['name'] for user in users_to_iterate])   

    for user in users_to_iterate:
        # If user has notifications toggled off, skip
        if(user['notifications'] == False):
            print(f"\tSkipping reminders for {user['name']}")
            continue
        print(f"\tSending reminders for {user['name']}")

        assignments = fetch_assignments(discord_id=user['id'], days=user['days_warning'])    
        incomplete_assignments = sum(len(l) for l in assignments.values())

        if(incomplete_assignments == 0):
            print(f"\t{user['name']} has no pending assignments!")
            continue

        user = bot.get_user(user['id'])

        embed = create_assignment_embed(assignments=assignments, days=user['days_warning'])
        embed.set_footer(text="(To toggle notifications off, type `/toggle-notifications False`)")
        
        await user.send(embed=embed)

        print(f"\tSuccessfully sent reminders for {user['name']}")

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
- Assignments that are submitted on Canvas will be automatically detected by this bot.
- However, if assignments are completed via 3rd-party websites (i.e Gradescope, Achieve, etc), this bot will not be able to detect completion.

"""
    embed.add_field(name="**__How does this bot work?__**", value=how_it_works, inline=False)

    embed.add_field(name="__**Below is a list of commands you can use with this bot!**__", value="\u200b", inline=False)

    setup_desc = """- Sets the API Token + Host URL for your Canvas account and whether to have Notifications On/Off + Days Warning. Upon first use, all arguments are required. *(They can each be updated later)*
- ❗**This command must be called before accessing any features of the bot.**"""
    embed.add_field(name="__`/settings`__", value=setup_desc, inline=False)
    
    delete_desc = """- Deletes your data from this bot's database. In order to confirm deletion, you must type `DELETE` in all CAPS exactly. """
    embed.add_field(name="__`/delete-user <confirm>`__", value=delete_desc, inline=False)

    get_assignments_desc = """- Returns the list of upcoming assignments from all Dashboard Courses due in `<days>` days (default 7 days).
- If `<update>` is set to True (default False), forces a request to Canvas (only use this if a newly posted assignment is not showing up)"""
    embed.add_field(name="__`/get-assignments <days> <update>`__", value=get_assignments_desc, inline=False)

    get_courses_desc = """- Returns a list of your Dashboard Courses
- For a course to appear on your Dashboard, it must be \"Favorited\" on Canvas. This is done for you by your school most of the time."""
    embed.add_field(name="__`/get-courses`__", value=get_courses_desc, inline=False)

    help_desc = """- Prints this message"""
    embed.add_field(name="__`/help`__", value=help_desc, inline=False)

    await interaction.response.send_message(embed=embed)
    return



class FirstSetup(discord.ui.Modal, title='Let\'s get you set up!'):
    url = discord.ui.TextInput(label='Your Canvas Page URL', required=True, placeholder='A URL like canvas.example.edu')
    
    token = discord.ui.TextInput(label='Your Canvas API Token', style=discord.TextStyle.paragraph, placeholder='A long string found on your Canvas Settings page.', required=True)

    notifications = discord.ui.TextInput(label="Notifications", placeholder="Yes | No   (Default: Yes)", required=False)

    days_warning = discord.ui.TextInput(label="Days Warning", placeholder="Any whole number greater than 0 (Default 7)", required=False)


    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()


class UpdateSettings(discord.ui.Modal, title='Empty fields will not be updated.'):
    url = discord.ui.TextInput(label='Your Canvas Page URL', required=False, placeholder='A URL like canvas.example.edu')
    
    token = discord.ui.TextInput(label='Your Canvas API Token', style=discord.TextStyle.paragraph, placeholder='A long string found on your Canvas Settings page.', required=False)

    notifications = discord.ui.TextInput(label="Notifications", placeholder="Yes | No", required=False)

    days_warning = discord.ui.TextInput(label="Days Warning", placeholder="Any whole number greater than 0", required=False)


    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()



@bot.tree.command(name="settings", description="Set or update your API Token, URL, and Notifications.")
async def settings(interaction: discord.Interaction):
    on_command(interaction)
    
    if(user_exists(interaction.user.id)):
        modal = UpdateSettings()
    else:
        print(f"\tNew user detected ({interaction.user.name}). Adding to database.")
        modal = FirstSetup()
    
    await interaction.response.send_modal(modal)

    errored = await modal.wait()

    print("View finished normally?", not errored)

    #If the view does not close properly (aka it times out or if the user presses Cancel/Esc), return and exit function.
    if(errored): return

    base_url = str(modal.url)
    token = str(modal.token)
    notifications = str(modal.notifications)
    days_warning = str(modal.days_warning)

    print(base_url, token, notifications, days_warning)

    # These if statements grab the URL instance and/or Token if they were left blank. 
    if(not user_exists(interaction.user.id)):
        # USER IS NEW TO DATABASE
        print(f"\tUser inputted: {base_url}")
        result = re.search(r"(\w+\.\w+\.\w+).*$", base_url)
        if result is None:
            print(f"\tError: Invalid URL")
            await interaction.followup.send(f"`{base_url}` is not a valid URL!", ephemeral=True)
            return
        base_url = result.group(1)
        print(f"\tExtracted group: {base_url}")

        if(days_warning == ""):
            days_warning = 7

    else:
        # USER ALREADY EXISTS IN DATABASE
        cursor.execute(f"SELECT canvas_instance, canvas_token, notifications, days_warning FROM users WHERE id={interaction.user.id}")
        user = cursor.fetchone()
        
        # If URL not given, fetch from database. Otherwise, run the Regex check to ensure it's valid and extract the right string
        if(len(base_url) == 0):
            base_url = user['canvas_instance']
        else:
            result = re.search(r"(\w+\.\w+\.\w+).*$", base_url)
            if result is None:
                print(f"\tError: Invalid URL")
                await interaction.followup.send(f"`{base_url}` is not a valid URL!", ephemeral=True)
                return
            base_url = result.group(1)
            print(f"\tExtracted group: {base_url}")
        
        # If Token not given, fetch from database
        if(len(token) == 0):
            token = user['canvas_token']
        
        # If Notifications not given, fetch from database. Otherwise, anything that's not YES means NO
        if(len(notifications) == 0):
            notifications = user['notifications']
        else:
            notifications = 1 if notifications.upper() == "YES" else 0
        
        # If Days not given, fetch from database. Otherwise
        if(len(days_warning) == 0):
            days_warning = user['days_warning']
        else:
            try:
                days_warning = int(days_warning)
            except ValueError:
                days_warning = user['days_warning']



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

    # Get the JSON output of the response
    canvas_json = canvas_request.json()


    # Update database
    user = (interaction.user.id, interaction.user.name, token, base_url, canvas_json['name'], canvas_json['id'], notifications, days_warning)
    print(str(user))

    if(user_exists(interaction.user.id)):
        q = f"UPDATE users SET canvas_instance = '{base_url}', canvas_name = '{canvas_json['name']}', canvas_id = {canvas_json['id']}, notifications = {notifications}, days_warning = {days_warning} WHERE id = {interaction.user.id}"
        print(q)
        cursor.execute(q)
    else:
        user = (interaction.user.id, interaction.user.name, token, base_url, canvas_json['name'], canvas_json['id'], notifications, days_warning)
        cursor.executemany("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?)", [user])
    
    con.commit()

    cursor.execute(f"SELECT * FROM users WHERE id = {interaction.user.id}")
    user_after_update = cursor.fetchone()

    await interaction.followup.send(f"Your settings have been updated to: URL - `{user_after_update['canvas_instance']}`, Notifications - `{user_after_update['notifications']}`, Days Warning - `{user_after_update['days_warning']}`", ephemeral=True)    
    return


@bot.tree.command(name="delete-user", description="Deletes your data from my database. WARNING: THIS CANNOT BE UNDONE")
@app_commands.describe(confirm="To confirm, type `DELETE` in all CAPS.")
async def delete_user(interaction: discord.Interaction, confirm: str):
    on_command(interaction)

    if(not user_exists(interaction.user.id)):
        print(f"\tUser {interaction.user.name} not found in database. Aborting.")
        await interaction.response.send_message("I couldn't find you in my database. Maybe you already deleted your data?", ephemeral=True)
        return
    
    if(confirm != "DELETE"):
        print(f"\tUser {interaction.user.name} did not type `DELETE` exactly: {confirm}")
        await interaction.response.send_message("Confirmation failed. Aborting delete command. In order to delete, please make sure you type `DELETE` exactly in all CAPS.", ephemeral=True)
        return

    if(confirm == "DELETE"):
        cursor.execute(f"DELETE FROM users WHERE id = {interaction.user.id}")
        cursor.execute(f"DELETE FROM assignments WHERE discord_id = {interaction.user.id}")
        con.commit()
    
    await interaction.response.send_message("Your data has successfully been deleted. You may add yourself back to the database by calling `/settings`.")



@bot.tree.command(name="get-assignments", description="Returns a list of your upcoming assignments.")
@app_commands.describe(days="Show assignments due within this many days (Default 7)", update="Forces a new call to Canvas to update assignments. Only use this if a newly posted assignment is not showing up.")
async def get_assignments(interaction: discord.Interaction, days: int=7, update: bool=False):
    on_command(interaction)
    
    if(not user_exists(interaction.user.id)):
        print(f"\tUser {interaction.user.name} not found in database. Aborting.")
        await interaction.response.send_message("It looks like you have not been added to my database yet. Please do so by calling `/settings`.")
        return
    
    cursor.execute(f"SELECT * FROM users WHERE id = {interaction.user.id}")
    user = cursor.fetchone()

    await interaction.response.defer()

    if(update or days > int(user['days_warning'])):
        # FORCE UPDATE
        assignments = fetch_assignments(discord_id=interaction.user.id, days=days)
    else:
        # READ FROM DB
        cursor.execute(f"SELECT * FROM assignments WHERE discord_id = {interaction.user.id} AND due_date BETWEEN datetime('now') AND datetime('now', '+{days + 1} days')")
        assignments = cursor.fetchall()

        print("Printing assignments")

    for assignment in assignments:
        print(assignment['assignment_name'])


    # if(len(assignments) == 0):
    #     interaction.response.send_message(f"Looks like there was a problem with the request. Please make sure your APIs have been set up correctly.\n(run `/help` for more info)")


    if(len(assignments) == 0):
        print(f"\t{interaction.user.name} has no pending assignments!")
        no_asgn = discord.Embed(title="Assignments", description=f"Congratulations {interaction.user.name}, you have no upcoming assignments!", color= discord.Color.green())
        await interaction.followup.send(embed=no_asgn)
        return
    
    embed = create_assignment_embed(assignments=assignments, days=days)
    
    await interaction.followup.send(embed=embed)

    print(f"\tSuccessfully sent reminders for {interaction.user.name}")

    return





@bot.tree.command(name="get-courses", description="Returns a list of your active courses.")
async def get_courses(interaction: discord.Interaction):
    on_command(interaction)

    if(not user_exists(interaction.user.id)):
        print(f"\tUser {interaction.user.name} not found in database. Aborting.")
        await interaction.response.send_message("It looks like you have not been added to my database yet. Please do so by calling `/settings`.")
        return
    
    cursor.execute(f"SELECT canvas_token, canvas_instance FROM users WHERE id = {interaction.user.id}")
    user = cursor.fetchone()

    canvas_token = user['canvas_token']
    canvas_instance = user['canvas_instance']
    
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



def main():
    bot.run(BOT_TOKEN)
    

if __name__ == '__main__':
    main()
