#!/usr/bin/env python3
"""
Update new task with comment and archive old forecast task
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

# Task GIDs
OLD_FORECAST_TASK_GID = '1212269459330774'
NEW_PREPRODUCTION_TASK_GID = '1212653503496839'

def add_comment_to_task(task_gid, comment_text):
    """Add a comment to a task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    payload = {
        "data": {
            "text": comment_text
        }
    }

    try:
        response = requests.post(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        print(f"✅ Added comment to task")
        return True
    except Exception as e:
        print(f"❌ Error adding comment: {e}")
        return False

def complete_task(task_gid):
    """Mark a task as complete (archives it)"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    payload = {
        "data": {
            "completed": True
        }
    }

    try:
        response = requests.put(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        print(f"✅ Archived/completed task")
        return True
    except Exception as e:
        print(f"❌ Error completing task: {e}")
        return False

def main():
    # Ann Barker's comment
    ann_comment = """**From Ann Barker (Forecast):**

I updated this due date to 2/1. Josh is leading the content.

The big idea is to start the 3 year Frontier with a recap of where we are headed (to onboard the people who missed it during the campaign/ newcomers) and to keep the vision fresh. .. so it will be a sizzler video of moments from vision nights etc...

I can do a video brief if you like. Just let me know how to best help."""

    print("📝 Adding Ann Barker's comment to new Preproduction task...")
    add_comment_to_task(NEW_PREPRODUCTION_TASK_GID, ann_comment)

    print("\n📦 Archiving original Forecast task...")
    complete_task(OLD_FORECAST_TASK_GID)

    print(f"\n✨ Done!")
    print(f"New task with comment: https://app.asana.com/0/1208336083003480/{NEW_PREPRODUCTION_TASK_GID}")

if __name__ == '__main__':
    main()
