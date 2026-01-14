#!/usr/bin/env python3
"""
Check which tasks are categorized as Pastoral/Strategic
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

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

# Custom field GIDs
PERCENT_ALLOCATION_FIELD_GID = '1208923995383367'
CATEGORY_FIELD_GID = '1209597964422013'  # Category field
PASTORAL_STRATEGIC_OPTION_GID = '1211901611025613'  # Pastoral/Strategic option

def fetch_pastoral_strategic_tasks():
    """Fetch all tasks categorized as Pastoral/Strategic"""
    pastoral_tasks = []

    for project_name, project_gid in ASANA_PROJECTS.items():
        print(f"\n📋 Fetching tasks from {project_name}...")

        try:
            response = requests.get(
                f'https://app.asana.com/api/1.0/projects/{project_gid}/tasks',
                headers=ASANA_HEADERS,
                params={
                    'opt_fields': 'gid,name,assignee.name,completed,custom_fields'
                }
            )

            if response.status_code == 200:
                tasks = response.json().get('data', [])

                for task in tasks:
                    if task.get('completed', False):
                        continue

                    # Extract category and percent allocation
                    category_gid = None
                    percent_allocation = 0

                    for field in task.get('custom_fields', []):
                        if field.get('gid') == CATEGORY_FIELD_GID:
                            # Category is an enum field
                            if field.get('enum_value'):
                                category_gid = field['enum_value'].get('gid')

                        if field.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                            percent_allocation = field.get('number_value', 0)

                    # Check if task is Pastoral/Strategic
                    if category_gid == PASTORAL_STRATEGIC_OPTION_GID:
                        pastoral_tasks.append({
                            'name': task.get('name', 'Untitled'),
                            'assignee': task.get('assignee', {}).get('name', 'Unassigned'),
                            'percent_allocation': percent_allocation * 100 if percent_allocation else 0,
                            'project': project_name
                        })
            else:
                print(f"  ⚠️ Error: {response.status_code}")

        except Exception as e:
            print(f"  ⚠️ Error fetching {project_name}: {e}")

    return pastoral_tasks

if __name__ == '__main__':
    print("🔍 Searching for Pastoral/Strategic tasks...\n")

    tasks = fetch_pastoral_strategic_tasks()

    print("\n" + "="*80)
    print("📊 PASTORAL/STRATEGIC TASKS")
    print("="*80)

    if not tasks:
        print("\nNo Pastoral/Strategic tasks found.")
    else:
        # Calculate total
        total_allocation = sum(t['percent_allocation'] for t in tasks)

        print(f"\nTotal Allocation: {total_allocation:.1f}%")
        print(f"Number of Tasks: {len(tasks)}\n")

        # Sort by allocation (highest first)
        sorted_tasks = sorted(tasks, key=lambda t: t['percent_allocation'], reverse=True)

        print(f"{'Task Name':<50} {'Assignee':<20} {'Allocation':<12} {'Project':<20}")
        print("-" * 102)

        for task in sorted_tasks:
            print(f"{task['name']:<50} {task['assignee']:<20} {task['percent_allocation']:>10.1f}% {task['project']:<20}")

        print("\n" + "="*80)
        print(f"TOTAL: {total_allocation:.1f}%")
        print("="*80)
