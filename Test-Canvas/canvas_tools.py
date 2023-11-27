#Standard Libraries
import requests
import os
import datetime
import json
import asyncio
import math
import re
import sqlite3
from collections import defaultdict

#Non-standard Libraries installed with pip
import discord
from discord import app_commands
from discord.utils import get
from discord.ext import commands, tasks

from dotenv import load_dotenv

import pytz

import datetime

con = sqlite3.connect("users.db")
cursor = con.cursor()
cursor.row_factory = sqlite3.Row

# Fetches assignments for a given user and returns a dictionary of courses -> assignments
def fetch_assignments(discord_id: int, days: int) -> dict:
    
    cursor.execute(f"SELECT * FROM users WHERE id = {discord_id}")
    user = cursor.fetchone()
    canvas_token = user['canvas_token']
    canvas_instance = user['canvas_instance']
    canvas_id = user['canvas_id']
    canvas_name = user['canvas_name']


    link = f"https://{canvas_instance}/api/v1/users/self/favorites/courses?access_token={canvas_token}"
    
    courses_request = requests.get(link)

    if(not validCode(courses_request.status_code)):            
        print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping user")
        return None
    
    courses_json = courses_request.json()

    # Delete all assignments associated with the user to flush out old out-dated assignments. We will store only relevant ones once we run a GET request.
    cursor.execute(f"DELETE FROM assignments WHERE discord_id = {discord_id}")


    params = {
        'include': ['submission'],
        'per_page': 100,
        'access_token': canvas_token
    }

    for course in courses_json:
        id = course['id']
        
        course_link = f"https://{canvas_instance}/api/v1/users/{canvas_id}/courses/{id}/assignments"
        

        while True:
            course_assignments = requests.get(course_link, params=params)
            
            if(not validCode(course_assignments.status_code)):            
                print(f"\tError with Canvas GET request: Status Code {courses_request.status_code} for:\n{courses_request.url}\nSkipping course")
                break

            course_assignments_json = course_assignments.json()

            for asgn in course_assignments_json:

                if(asgn['due_at'] is None):
                    continue

                due_date = datetime.datetime.strptime(asgn['due_at'], '%Y-%m-%dT%H:%M:%SZ')
                time_until_due = due_date - datetime.datetime.utcnow()

                # We will insert assigments strictly based on the user's days_warning value. If this was called via /get-assignments, we still insert
                # for the same number of days into the database, but we will return a different value when reading from the database.
                if time_until_due > datetime.timedelta(days=0) and time_until_due <= datetime.timedelta(days=user['days_warning']+1):
                    
                    due_date_SQL = due_date.strftime("%Y-%m-%d %H:%M:%S")
                    submitted = 1 if asgn['submission']['submitted_at'] != None else 0
                    data = (discord_id, canvas_name, asgn['name'], asgn['id'], course['name'], course['id'], due_date_SQL, submitted, asgn['html_url'])
                    cursor.executemany(f"INSERT INTO assignments VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", [data])

                    print(f"\t{asgn['name']}\t\t\t{time_until_due}")


            
            if "next" not in course_assignments.links.keys():
                break
            else:
                course_link = course_assignments.links['next']['url']
        con.commit()
    cursor.execute(f"SELECT * FROM assignments WHERE discord_id = {discord_id} AND due_date BETWEEN datetime('now') AND datetime('now', '+{days + 1} days')")
    assignments = cursor.fetchall()
    print("length of assignment list", len(assignments))
    
    return assignments

# Given a list of assignments, constructs an embed that displays them on Discord
def create_assignment_embed(assignments: dict, days: int) -> discord.Embed:
    #assignments: List[sqlite3.Row objects]
    #each assignment: (discord_id, canvas_name, name, assignment_id, course_name, course_id, due_date, submitted)
    
    embed = discord.Embed(title="Assignment Reminder", description=f"Hey! here is a list of assignments that are due in the next {days} days!", color=discord.Color.green())

    def def_value():
        return []
    assignment_dictionary = defaultdict(def_value)
    
    for assignment in assignments:
        assignment_dictionary[assignment['course_name']].append(assignment)


    for course_name, assignment_list in assignment_dictionary.items():
        if(len(assignment_list) > 0):
            full = False
            msg = ""
            for assignment in assignment_list:
                emoji = "✅" if assignment['submitted'] == 1 else "⛔"
                if(assignment['submitted'] == 0):
                    embed.color = discord.Color.red()
                
                due_date = datetime.datetime.strptime(assignment['due_date'], '%Y-%m-%d %H:%M:%S')
                due_in = due_date - datetime.datetime.utcnow()
                line = f"- {emoji} *{assignment['assignment_name']}* \n    - Due in {'**' * (due_in < datetime.timedelta(days=3))}{due_in.days} days, {math.floor(due_in.seconds/3600)} hours, and {math.ceil(due_in.seconds%3600 / 60)} minutes{'**' * (due_in < datetime.timedelta(days=3))}\n  - Link: {assignment['url']}\n"
                if(len(msg) + len(line) > 1024):
                    full = True
                    embed.add_field(name=course_name, value=msg, inline=False)
                    msg = ""
                msg += line
            embed.add_field(name="\u200b" if full else course_name, value=msg, inline=False)
    
    return embed


# Returns True if HTTP status code is successfull (aka 200 - 299)
def validCode(status_code):
    return (status_code >= 200 and status_code < 300)


# Audits the current command running along with who called it and where it was called (guild channel/dm channel)
def on_command(interaction):
    if(interaction.guild is None):
        print(f"-- Direct Message with {interaction.user.name}: `/{interaction.command.name}` by {interaction.user.name}")
    else:
        print(f"-- {interaction.guild.name}({interaction.guild.id}): `/{interaction.command.name}` by {interaction.user.name}")

    return

# Checks if the user with the specified id exists in the database. Returns True if yes, False if no
def user_exists(id):
    cursor.execute(f"SELECT * FROM users WHERE id={id}")
    return cursor.fetchone() != None


def main():
    return

if __name__ == "__main__":
    main()
