#!/usr/bin/env python3
"""
Capacity Snapshot Script
Captures daily team capacity utilization and stores it in CSV for historical tracking
"""
import requests
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Team capacity configuration (matches generate_dashboard.py)
TEAM_CAPACITY = {
    'Zach Welliver': {'max': 50},
    'Nick Clark': {'max': 100},
    'Adriel Abella': {'max': 100},
    'John Meyer': {'max': 30}
}

# Asana configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

PROJECT_GIDS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}

PERCENT_ALLOCATION_FIELD_GID = '1208923995383367'
HISTORY_FILE = os.path.expanduser("~/Scripts/StudioProcesses/Reports/capacity_history.csv")

def fetch_team_capacity():
    """Fetch current team capacity from Asana"""
    team_usage = {name: 0 for name in TEAM_CAPACITY.keys()}

    for project_name, project_gid in PROJECT_GIDS.items():
        try:
            endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
            params = {
                'opt_fields': 'gid,name,assignee.name,custom_fields,completed'
            }

            response = requests.get(endpoint, headers=ASANA_HEADERS, params=params)

            if response.status_code == 200:
                tasks = response.json().get('data', [])

                for task in tasks:
                    # Skip completed tasks
                    if task.get('completed', False):
                        continue

                    # Get assignee
                    assignee = task.get('assignee')
                    if not assignee:
                        continue

                    assignee_name = assignee.get('name', '')

                    # Find Percent Allocation custom field
                    allocation_pct = 0
                    for field in task.get('custom_fields', []):
                        if field.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                            allocation_pct = (field.get('number_value', 0) or 0) * 100
                            break

                    # Add to team member's usage
                    if assignee_name in team_usage:
                        team_usage[assignee_name] += allocation_pct

        except Exception as e:
            print(f"Warning: Could not fetch tasks from {project_name}: {e}")
            continue

    return team_usage

def save_capacity_snapshot(team_usage):
    """Save capacity snapshot to CSV"""
    today = datetime.now().strftime('%Y-%m-%d')

    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(HISTORY_FILE)

    # Ensure Reports directory exists
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if file is new
        if not file_exists:
            writer.writerow(['date', 'team_member', 'current_capacity', 'max_capacity', 'utilization_percent'])

        # Write each team member's data
        for name, current in team_usage.items():
            max_capacity = TEAM_CAPACITY[name]['max']
            utilization = (current / max_capacity * 100) if max_capacity > 0 else 0
            writer.writerow([today, name, f"{current:.1f}", max_capacity, f"{utilization:.1f}"])

        # Calculate and write team total
        total_current = sum(team_usage.values())
        total_max = sum(config['max'] for config in TEAM_CAPACITY.values())
        total_utilization = (total_current / total_max * 100) if total_max > 0 else 0
        writer.writerow([today, 'Team Total', f"{total_current:.1f}", total_max, f"{total_utilization:.1f}"])

    print(f"✅ Capacity snapshot saved for {today}")
    print(f"   Team utilization: {total_utilization:.1f}%")

def main():
    """Main execution"""
    if not ASANA_PAT:
        print("❌ ASANA_PAT not found in environment")
        return

    print("📸 Capturing capacity snapshot...")
    team_usage = fetch_team_capacity()
    save_capacity_snapshot(team_usage)

if __name__ == "__main__":
    main()
