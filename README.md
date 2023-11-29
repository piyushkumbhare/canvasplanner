# Canvas Application
This is an application within Discord that tracks the completion of your assignments on Canvas. It will send you periodic reminders of upcoming incomplete assignments so you never miss any deadlines again!

## How do I set it up?

You'll only need 2 things to get set up:
- Canvas API Token
- URL of your Canvas page

Both of these can be found on your Canvas desktop page.

Your API Token can be found by navigating to Profile > Settings > (Scroll Down) > [+ New Token]

Your Canvas URL is simply the URL you access Canvas through (something like canvas.example.edu). You can just copy paste your entire URL if you're not sure.

Once you have both of these values, call `/settings` in the DMs with this bot. It will prompt you for the values above as well as some notification settings. Fill these in and hit `Submit`.

That's it! You'll now get notifications about your upcoming assignments every morning. You can also query info about your assignments and courses via commands like `/get-assignments` and `/get-courses`. 

## How does it work?

This application uses Canvas' API Endpoints to get information about your courses and assignments. The information that is tracked is:
- Course names
- Assignment names
- Due dates
- Whether you've submitted something
- Direct HTML URL to assignments (so you can access them easily from Disord)

To learn more about the application, run `/help`.

## Deleting your data

If you want to stop sharing your data with the application, you can do 1 of 2 things (or both).

1. Change/Delete the Canvas API Token associated with this application (this is done on Canvas)
2. Run `/delete-user` in a DM with the bot (this deletes your user and assignment information from this application's database)

