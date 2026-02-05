#!/usr/bin/env python3
"""
Debug script to check the current status of Q1 Frontier Update task
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

# Project GIDs
PROJECTS = {
    'Post Production': '1209581743268502',
    'Production': '1209597979075357',
    'Preproduction': '1208336083003480',
    'Forecast': '1212059678473189'
}

def find_q1_frontier_task():
    """Find the Q1 Frontier Update task across all projects"""
    print("🔍 Searching for Q1 Frontier Update task...")

    for project_name, project_id in PROJECTS.items():
        print(f"\n📂 Checking {project_name}...")

        try:
            url = f'https://app.asana.com/api/1.0/projects/{project_id}/tasks'
            params = {
                'opt_fields': 'gid,name,completed,custom_fields,assignee.name,due_on'
            }
            response = requests.get(url, headers=ASANA_HEADERS, params=params)

            if response.status_code == 200:
                tasks = response.json().get('data', [])

                for task in tasks:
                    if 'Q1 Frontier' in task.get('name', ''):
                        print(f"\n✅ Found: {task['name']}")
                        print(f"   GID: {task['gid']}")
                        print(f"   Project: {project_name}")
                        print(f"   Assignee: {task.get('assignee', {}).get('name', 'Unassigned')}")
                        print(f"   Due: {task.get('due_on', 'No due date')}")
                        print(f"   Completed: {task.get('completed', False)}")

                        # Check custom fields
                        print(f"\n📋 Custom Fields:")
                        for field in task.get('custom_fields', []):
                            field_name = field.get('name', 'Unknown')
                            if field.get('enum_value'):
                                field_value = field['enum_value'].get('name', 'N/A')
                            elif field.get('text_value'):
                                field_value = field['text_value']
                            elif field.get('number_value') is not None:
                                field_value = field['number_value']
                            else:
                                field_value = field.get('display_value', 'N/A')

                            print(f"   {field_name}: {field_value}")

                        return task

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n❌ Q1 Frontier Update task not found")
    return None

if __name__ == "__main__":
    find_q1_frontier_task()