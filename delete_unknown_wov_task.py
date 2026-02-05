#!/usr/bin/env python3
"""
Delete the 'WOV - Unknown Talent' task that was created as a duplicate
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

# Asana setup
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
PRODUCTION_PROJECT_GID = "1209597979075357"
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

def find_unknown_talent_task():
    """Find the WOV - Unknown Talent task in Production project"""
    url = f"https://app.asana.com/api/1.0/projects/{PRODUCTION_PROJECT_GID}/tasks"
    params = {"opt_fields": "name,gid,completed"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']

        for task in tasks:
            if not task.get('completed') and 'Unknown Talent' in task.get('name', ''):
                print(f"📋 Found task: {task['name']} (GID: {task['gid']})")
                return task

        print("❌ No 'Unknown Talent' task found")
        return None

    except Exception as e:
        print(f"❌ Error finding task: {e}")
        return None

def delete_task(task_gid, task_name):
    """Delete a task from Asana"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"

    try:
        response = requests.delete(url, headers=ASANA_HEADERS)
        response.raise_for_status()
        print(f"✅ Successfully deleted task: {task_name}")
        return True

    except Exception as e:
        print(f"❌ Error deleting task: {e}")
        return False

def main():
    print("🔍 Looking for 'WOV - Unknown Talent' task...")

    unknown_task = find_unknown_talent_task()
    if unknown_task:
        print(f"\n🗑️  Deleting duplicate task...")
        success = delete_task(unknown_task['gid'], unknown_task['name'])

        if success:
            print("\n✅ Task cleanup complete!")
        else:
            print("\n❌ Failed to delete task")
    else:
        print("\n📋 No unknown talent tasks found to delete")

if __name__ == "__main__":
    main()