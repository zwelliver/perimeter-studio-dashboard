#!/usr/bin/env python3
"""
Debug script to check what task progress value is being picked up for Q1 Frontier task
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

# Field GIDs (from the dashboard script)
TASK_PROGRESS_FIELD_GID = '1209598240843051'
POST_PRODUCTION_PROJECT_GID = '1209581743268502'

def debug_task_progress():
    """Debug task progress detection for Q1 Frontier task"""
    print("🔍 Debugging task progress detection...")

    try:
        url = f'https://app.asana.com/api/1.0/projects/{POST_PRODUCTION_PROJECT_GID}/tasks'
        params = {
            'opt_fields': 'gid,name,custom_fields.gid,custom_fields.name,custom_fields.display_value,custom_fields.enum_value'
        }
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json().get('data', [])

        for task in tasks:
            if 'Q1 Frontier' in task.get('name', ''):
                print(f"\n✅ Found: {task['name']}")
                print(f"   GID: {task['gid']}")

                # Simulate the NEW dashboard script logic
                task_progress = None
                task_progress_values = []

                print(f"\n📋 All Custom Fields:")
                for field in task.get('custom_fields', []):
                    field_name = field.get('name', 'Unknown')
                    field_gid = field.get('gid', 'Unknown')

                    if field.get('display_value'):
                        field_value = field.get('display_value')
                    elif field.get('enum_value'):
                        field_value = field['enum_value'].get('name', 'N/A')
                    else:
                        field_value = 'N/A'

                    print(f"   {field_name} (GID: {field_gid}): {field_value}")

                    # Collect ALL Task Progress fields by name (NEW LOGIC)
                    if field_name == 'Task Progress' and field.get('display_value'):
                        task_progress_values.append(field.get('display_value'))

                print(f"\n🎯 NEW Dashboard script logic:")
                print(f"   All Task Progress values: {task_progress_values}")

                # Apply the NEW prioritization logic
                if task_progress_values:
                    priority_order = ['In Progress', 'Scheduled', 'Needs Scheduling', 'Filmed', 'Offloaded']
                    for status in priority_order:
                        if status in task_progress_values:
                            task_progress = status
                            print(f"   ↳ Using prioritized status: {task_progress}")
                            break
                    if not task_progress:
                        task_progress = task_progress_values[0]
                        print(f"   ↳ Using first available: {task_progress}")

                print(f"\n🏁 NEW Final task_progress value: {task_progress}")

                print(f"\n🏁 Final task_progress value: {task_progress}")

                # Check if this would be flagged as at-risk
                if task_progress in ['Filmed', 'Offloaded']:
                    print(f"   ❌ Would be flagged as at-risk: 'not yet in progress'")
                elif task_progress == 'In Progress':
                    print(f"   ✅ Would NOT be flagged as at-risk: task is in progress")
                else:
                    print(f"   ❓ Unknown risk status for: {task_progress}")

                return

    except Exception as e:
        print(f"❌ Error: {e}")

    print("❌ Q1 Frontier task not found")

if __name__ == "__main__":
    debug_task_progress()