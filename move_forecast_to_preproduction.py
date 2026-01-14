#!/usr/bin/env python3
"""
Move Forecast Task to Preproduction
Finds a task in Forecast project and creates it in Preproduction with all details
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Asana configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

FORECAST_PROJECT_GID = '1212059678473189'
PREPRODUCTION_PROJECT_GID = '1208336083003480'

def find_task_by_name(project_gid, task_name):
    """Find a task in a project by name"""
    url = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
    params = {"opt_fields": "name,notes,due_on,assignee.name,custom_fields"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']

        for task in tasks:
            if task_name.lower() in task['name'].lower():
                return task

        return None
    except Exception as e:
        print(f"Error finding task: {e}")
        return None

def get_task_comments(task_gid):
    """Get all comments/stories from a task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    params = {"opt_fields": "text,created_by.name,created_at"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        stories = response.json()['data']

        comments = []
        for story in stories:
            if story.get('text'):  # Only get actual comments, not system updates
                comments.append({
                    'text': story['text'],
                    'author': story.get('created_by', {}).get('name', 'Unknown'),
                    'created_at': story.get('created_at', '')
                })

        return comments
    except Exception as e:
        print(f"Error getting comments: {e}")
        return []

def get_full_task_details(task_gid):
    """Get complete task details including description"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    params = {"opt_fields": "name,notes,due_on,assignee,custom_fields,html_notes"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        print(f"Error getting task details: {e}")
        return None

def create_preproduction_task(task_data, comments):
    """Create a new task in Preproduction project with all details"""

    # Build comprehensive notes from original task + comments
    notes = f"**[Moved from Forecast]**\n\n"

    if task_data.get('notes'):
        notes += f"{task_data['notes']}\n\n"

    if comments:
        notes += "---\n**Comments from Forecast:**\n\n"
        for comment in comments:
            notes += f"**{comment['author']}** ({comment['created_at'][:10]}):\n{comment['text']}\n\n"

    # Prepare task creation payload
    payload = {
        "data": {
            "name": task_data['name'],
            "notes": notes,
            "projects": [PREPRODUCTION_PROJECT_GID]
        }
    }

    # Add due date if exists
    if task_data.get('due_on'):
        payload['data']['due_on'] = task_data['due_on']

    # Add assignee if exists
    if task_data.get('assignee') and task_data['assignee'].get('gid'):
        payload['data']['assignee'] = task_data['assignee']['gid']

    url = "https://app.asana.com/api/1.0/tasks"

    try:
        response = requests.post(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        new_task = response.json()['data']
        print(f"✅ Created new task in Preproduction: {new_task['name']}")
        print(f"   Task GID: {new_task['gid']}")
        print(f"   URL: https://app.asana.com/0/{PREPRODUCTION_PROJECT_GID}/{new_task['gid']}")
        return new_task
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return None

def main():
    task_name = "Q1 Frontier Update"

    print(f"🔍 Searching for '{task_name}' in Forecast project...")

    # Find the task in Forecast
    task = find_task_by_name(FORECAST_PROJECT_GID, task_name)

    if not task:
        print(f"❌ Task '{task_name}' not found in Forecast project")
        return

    print(f"✅ Found task: {task['name']}")
    print(f"   Task GID: {task['gid']}")

    # Get full task details
    print(f"\n📋 Getting full task details...")
    full_task = get_full_task_details(task['gid'])

    if not full_task:
        print("❌ Could not get task details")
        return

    # Get comments
    print(f"💬 Getting task comments...")
    comments = get_task_comments(task['gid'])
    print(f"   Found {len(comments)} comment(s)")

    # Display what we found
    print(f"\n📊 Task Details:")
    print(f"   Name: {full_task['name']}")
    print(f"   Notes: {full_task.get('notes', 'None')[:100]}...")
    if full_task.get('assignee'):
        print(f"   Assignee: {full_task['assignee'].get('name', 'Unknown')}")
    if full_task.get('due_on'):
        print(f"   Due Date: {full_task['due_on']}")

    # Create in Preproduction
    print(f"\n🚀 Creating task in Preproduction project...")
    new_task = create_preproduction_task(full_task, comments)

    if new_task:
        print(f"\n✨ Success! Task moved from Forecast to Preproduction")
        print(f"\nNext steps:")
        print(f"1. Review the new task: https://app.asana.com/0/{PREPRODUCTION_PROJECT_GID}/{new_task['gid']}")
        print(f"2. Complete or archive the original forecast task if needed")

if __name__ == '__main__':
    main()
