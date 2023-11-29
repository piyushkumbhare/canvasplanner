import requests
import json
import datetime

with open('users.json', 'r') as f:
    userInfo = json.load(f)
    print(f"\tLoaded info for {len(userInfo)} users.")

user_id = "268126708413104128"

canvas_instance = userInfo[user_id]['canvas-instance']
canvas_token = userInfo[user_id]['canvas-token']
canvas_id = userInfo[user_id]['canvas-id']
days = userInfo[user_id]['days-warning']

courses_request = requests.get(f"https://{canvas_instance}/api/v1/users/self/favorites/courses?access_token={canvas_token}")

courses_json = courses_request.json()


assignments = {}

for course in courses_json:
    print()
    print(course['name'])
    id = course['id']
    params = {
        'include': ['submission'],
        'per_page': 5000,
        'access_token': canvas_token
    }
    link = f"https://{canvas_instance}/api/v1/users/{canvas_id}/courses/{id}/assignments?access_token={canvas_token}"
    course_assignments = requests.get(link, params=params)
    
    
    # for key, value in course_assignments.links.items():
    #     print(key, value)


    course_assignments_json = course_assignments.json()
    assignments[course['name']] = []

    print(link)

    for asgn in course_assignments_json:

        if(asgn['due_at'] is None):
            continue

    
        time_until_due = datetime.datetime.strptime(asgn['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.utcnow()
        # print(f"\t{asgn['name']}\t\t\t{time_until_due}")
        if(time_until_due > datetime.timedelta(days=0)):
            print(asgn['name'], time_until_due)

        if time_until_due > datetime.timedelta(days=0) and time_until_due <= datetime.timedelta(days=days):
            assignments[course['name']].append((asgn['name'], time_until_due, asgn['submission']['submitted_at'] != None, asgn['html_url']))

    if("next" in course_assignments.links.keys()):
        print(course_assignments.links["next"])
        course_assignments = requests.get(course_assignments.links["next"]["url"], params=params)

        course_assignments_json = course_assignments.json()
        assignments[course['name']] = []
        for asgn in course_assignments_json:

            if(asgn['due_at'] is None):
                continue

        
            time_until_due = datetime.datetime.strptime(asgn['due_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.datetime.utcnow()
            # print(f"\t{asgn['name']}\t\t\t{time_until_due}")
            if(time_until_due > datetime.timedelta(days=0)):
                print(asgn['name'], "Due in: ", time_until_due)

            if time_until_due > datetime.timedelta(days=0) and time_until_due <= datetime.timedelta(days=days):
                assignments[course['name']].append((asgn['name'], time_until_due, asgn['submission']['submitted_at'] != None, asgn['html_url']))
