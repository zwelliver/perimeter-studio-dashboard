#!/usr/bin/env python3
"""
Show current active tasks categorized as Pastoral/Strategic
to explain the 42.7% allocation shown in the weighted_allocation_report.csv
"""

import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime

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
CATEGORY_FIELD_GID = '1209597964422013'
PASTORAL_STRATEGIC_OPTION_GID = '1211901611025613'

def fetch_all_active_tasks_with_categories():
    """Fetch all active tasks with their categories and allocations"""
    all_tasks = []

    for project_name, project_gid in ASANA_PROJECTS.items():
        print(f"📋 Fetching from {project_name}...", end=' ')

        try:
            response = requests.get(
                f'https://app.asana.com/api/1.0/projects/{project_gid}/tasks',
                headers=ASANA_HEADERS,
                params={
                    'opt_fields': 'gid,name,assignee.name,completed,custom_fields,start_on,due_on'
                }
            )

            if response.status_code == 200:
                tasks = response.json().get('data', [])
                task_count = 0

                for task in tasks:
                    if task.get('completed', False):
                        continue

                    # Extract fields
                    category_name = None
                    category_gid = None
                    percent_allocation = 0

                    for field in task.get('custom_fields', []):
                        if field.get('gid') == CATEGORY_FIELD_GID:
                            if field.get('enum_value'):
                                category_gid = field['enum_value'].get('gid')
                                category_name = field['enum_value'].get('name')

                        if field.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                            percent_allocation = field.get('number_value', 0)

                    # Store all tasks with categories
                    if category_name:
                        all_tasks.append({
                            'name': task.get('name', 'Untitled'),
                            'assignee': task.get('assignee', {}).get('name', 'Unassigned'),
                            'percent_allocation': percent_allocation * 100 if percent_allocation else 0,
                            'category': category_name,
                            'category_gid': category_gid,
                            'project': project_name,
                            'start_on': task.get('start_on'),
                            'due_on': task.get('due_on')
                        })
                        task_count += 1

                print(f"✓ {task_count} tasks with categories")
            else:
                print(f"⚠️ Error: {response.status_code}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

    return all_tasks

if __name__ == '__main__':
    print("🔍 Analyzing current active tasks by category...\n")

    tasks = fetch_all_active_tasks_with_categories()

    if not tasks:
        print("No tasks with categories found.")
    else:
        # Convert to dataframe for easier analysis
        df = pd.DataFrame(tasks)

        # Calculate totals by category
        category_totals = df.groupby('category')['percent_allocation'].sum().sort_values(ascending=False)
        total_allocation = category_totals.sum()

        print("="*80)
        print("📊 CURRENT ALLOCATION BY CATEGORY")
        print("="*80)
        print(f"\nCategory                   Allocation    % of Total")
        print("-" * 60)
        for category, allocation in category_totals.items():
            pct_of_total = (allocation / total_allocation * 100) if total_allocation > 0 else 0
            print(f"{category:<25} {allocation:>10.1f}%    {pct_of_total:>6.1f}%")
        print("-" * 60)
        print(f"{'TOTAL':<25} {total_allocation:>10.1f}%")

        # Show Pastoral/Strategic tasks in detail
        pastoral_tasks = df[df['category'] == 'Pastoral/Strategic'].copy()

        if not pastoral_tasks.empty:
            print("\n" + "="*80)
            print("📋 PASTORAL/STRATEGIC TASKS (Making up the 42.7%)")
            print("="*80)

            # Sort by allocation
            pastoral_tasks = pastoral_tasks.sort_values('percent_allocation', ascending=False)

            total_pastoral = pastoral_tasks['percent_allocation'].sum()
            print(f"\nTotal Pastoral/Strategic Allocation: {total_pastoral:.1f}%")
            print(f"Number of Tasks: {len(pastoral_tasks)}\n")

            for idx, task in pastoral_tasks.iterrows():
                print(f"{task['name']}")
                print(f"  Project: {task['project']}")
                print(f"  Assignee: {task['assignee']}")
                print(f"  Allocation: {task['percent_allocation']:.1f}%")
                if task['due_on']:
                    print(f"  Due: {task['due_on']}")
                print()

        else:
            print("\n⚠️ No Pastoral/Strategic tasks found")
            print("This suggests the category field may not be set in Asana yet.")
