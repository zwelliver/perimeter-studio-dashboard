#!/usr/bin/env python3
"""
Debug script to check what task data is being passed to create_or_update_event
"""

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(".env")

# Asana config
ASANA_PAT = os.getenv('ASANA_PAT_SCORER')
ASANA_HEADERS = {
    'Authorization': f'Bearer {ASANA_PAT}',
    'Content-Type': 'application/json'
}

ASANA_PROJECTS = {
    'Production': '1209597979075357',
}

def debug_task_data():
    """Debug the task data structure being created"""
    print("🔍 Debugging task data structure...")

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
                        print(f"\n✅ Raw task from Asana: {task}")

                        # Simulate the processing logic (prefer due_at over due_on)
                        due_date = None
                        due_datetime = None
                        if task.get('due_at'):
                            due_datetime_obj = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
                            due_date = due_datetime_obj.strftime('%Y-%m-%d')
                            due_datetime = task['due_at']
                        elif task.get('due_on'):
                            due_date = task['due_on']
                            due_datetime = None

                        processed_task = {
                            'gid': task['gid'],
                            'name': task['name'],
                            'due_date': due_date,
                            'due_datetime': due_datetime,
                            'project': project_name,
                            'modified_at': task.get('modified_at')
                        }

                        print(f"\n📋 Processed task data: {processed_task}")
                        break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    debug_task_data()