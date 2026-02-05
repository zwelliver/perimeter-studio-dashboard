#!/usr/bin/env python3
"""
Debug script to check the actual due_at time for Unlimited Grace - January task
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

# Asana config
ASANA_PAT = os.getenv('ASANA_PAT_SCORER')
ASANA_HEADERS = {
    'Authorization': f'Bearer {ASANA_PAT}',
    'Content-Type': 'application/json'
}

ASANA_PROJECTS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}

def debug_task_times():
    """Debug the actual due_at times for tasks"""
    print("🔍 Debugging Asana task times...")

    for project_name, project_id in ASANA_PROJECTS.items():
        print(f"\n📂 Checking {project_name}...")

        try:
            url = f'https://app.asana.com/api/1.0/projects/{project_id}/tasks'
            params = {
                'opt_fields': 'gid,name,completed,due_on,due_at,modified_at'
            }
            response = requests.get(url, headers=ASANA_HEADERS, params=params)

            if response.status_code == 200:
                tasks = response.json().get('data', [])
                for task in tasks:
                    if task.get('completed'):
                        continue

                    if 'Unlimited Grace' in task.get('name', '') and 'January' in task.get('name', ''):
                        print(f"\n✅ Found: {task['name']}")
                        print(f"   GID: {task['gid']}")
                        print(f"   due_on: {task.get('due_on')}")
                        print(f"   due_at: {task.get('due_at')}")
                        print(f"   modified_at: {task.get('modified_at')}")
                        break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    debug_task_times()