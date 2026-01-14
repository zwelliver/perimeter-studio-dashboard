#!/usr/bin/env python3
"""
Generate forward-looking capacity forecast based on upcoming Asana tasks
"""

import os
import csv
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv(".env")

# Asana Configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

PROJECTS = {
    "Preproduction": "1208336083003480",
    "Production": "1209597979075357",
    "Post Production": "1209581743268502"
}

# Custom Fields
PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"
START_DATE_FIELD_GID = "1211967927674488"

# Team member capacities (max hours per day)
TEAM_CAPACITIES = {
    "Zach Welliver": 50,
    "Nick Clark": 100,
    "Adriel Abella": 100,
    "John Meyer": 30
}

def get_upcoming_tasks():
    """Fetch all upcoming tasks from Asana projects"""
    all_tasks = []

    print("📥 Fetching upcoming tasks from Asana...")

    for project_name, project_gid in PROJECTS.items():
        print(f"  Fetching {project_name}...")

        url = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
        params = {
            "opt_fields": "name,assignee.name,due_on,start_on,completed,custom_fields"
        }

        response = requests.get(url, headers=ASANA_HEADERS, params=params)

        if response.status_code == 200:
            tasks = response.json()["data"]
            all_tasks.extend(tasks)
        else:
            print(f"    ⚠️  Error fetching {project_name}: {response.status_code}")

    print(f"✅ Fetched {len(all_tasks)} total tasks\n")
    return all_tasks

def extract_allocation(task):
    """Extract percent allocation from custom fields"""
    custom_fields = task.get("custom_fields", [])

    for field in custom_fields:
        if field.get("gid") == PERCENT_ALLOCATION_FIELD_GID:
            value = field.get("number_value")
            return float(value) if value is not None else 0.0

    return 0.0

def extract_start_date(task):
    """Extract start date from task"""
    # Try standard start_on field first
    if task.get("start_on"):
        return datetime.strptime(task["start_on"], "%Y-%m-%d").date()

    # Try custom field
    custom_fields = task.get("custom_fields", [])
    for field in custom_fields:
        if field.get("gid") == START_DATE_FIELD_GID:
            date_value = field.get("date_value")
            if date_value and isinstance(date_value, dict):
                date_str = date_value.get("date")
                if date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()

    # Fallback to due date if available
    if task.get("due_on"):
        return datetime.strptime(task["due_on"], "%Y-%m-%d").date()

    return None

def extract_due_date(task):
    """Extract due date from task"""
    if task.get("due_on"):
        return datetime.strptime(task["due_on"], "%Y-%m-%d").date()
    return None

def generate_forecast(tasks, days_forward=60):
    """Generate capacity forecast for upcoming days"""

    print(f"📊 Generating {days_forward}-day capacity forecast...\n")

    # Filter for upcoming incomplete tasks
    upcoming_tasks = []
    today = datetime.now().date()

    for task in tasks:
        # Skip completed tasks
        if task.get("completed"):
            continue

        # Must have assignee
        assignee = task.get("assignee")
        if not assignee or not assignee.get("name"):
            continue

        # Must have allocation
        allocation = extract_allocation(task)
        if allocation == 0:
            continue

        # Must have date info
        start_date = extract_start_date(task)
        due_date = extract_due_date(task)

        if not start_date and not due_date:
            continue

        # Use start_date or due_date as work date
        work_date = start_date or due_date

        # Skip past tasks
        if work_date < today:
            continue

        # Skip tasks too far in future
        if work_date > today + timedelta(days=days_forward):
            continue

        upcoming_tasks.append({
            "name": task["name"],
            "assignee": assignee["name"],
            "allocation": allocation,
            "start_date": start_date,
            "due_date": due_date,
            "work_date": work_date
        })

    print(f"   Found {len(upcoming_tasks)} relevant upcoming tasks\n")

    # Calculate daily capacity by team member
    daily_capacity = {}

    for day_offset in range(days_forward + 1):
        current_date = today + timedelta(days=day_offset)

        # Initialize capacity for this date
        date_capacity = {member: 0.0 for member in TEAM_CAPACITIES.keys()}

        # Add allocations for tasks on this date
        for task in upcoming_tasks:
            if task["work_date"] == current_date:
                assignee = task["assignee"]
                if assignee in date_capacity:
                    date_capacity[assignee] += task["allocation"]

        daily_capacity[current_date] = date_capacity

    return daily_capacity

def save_forecast_csv(daily_capacity, output_path):
    """Save forecast to CSV in same format as capacity_history.csv"""

    print(f"💾 Saving forecast to {output_path}...")

    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['date', 'team_member', 'current_capacity', 'max_capacity', 'utilization_percent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for date in sorted(daily_capacity.keys()):
            capacities = daily_capacity[date]

            # Write individual team members
            team_total_current = 0
            team_total_max = 0

            for member, current in capacities.items():
                max_capacity = TEAM_CAPACITIES[member]
                utilization = (current / max_capacity * 100) if max_capacity > 0 else 0

                writer.writerow({
                    'date': date.strftime('%Y-%m-%d'),
                    'team_member': member,
                    'current_capacity': round(current, 1),
                    'max_capacity': max_capacity,
                    'utilization_percent': round(utilization, 1)
                })

                team_total_current += current
                team_total_max += max_capacity

            # Write team total
            team_utilization = (team_total_current / team_total_max * 100) if team_total_max > 0 else 0

            writer.writerow({
                'date': date.strftime('%Y-%m-%d'),
                'team_member': 'Team Total',
                'current_capacity': round(team_total_current, 1),
                'max_capacity': team_total_max,
                'utilization_percent': round(team_utilization, 1)
            })

    print(f"✅ Forecast saved!\n")

def combine_historical_and_forecast():
    """Combine historical capacity data with forecast"""

    print("🔄 Combining historical and forecast data...")

    historical_path = "Reports/capacity_history.csv"
    forecast_path = "Reports/capacity_forecast.csv"
    combined_path = "Reports/capacity_combined.csv"

    # Read both files
    combined_data = []

    # Read historical
    if os.path.exists(historical_path):
        with open(historical_path, 'r') as f:
            reader = csv.DictReader(f)
            combined_data.extend(list(reader))

    # Read forecast
    if os.path.exists(forecast_path):
        with open(forecast_path, 'r') as f:
            reader = csv.DictReader(f)
            forecast_data = list(reader)

            # Only add forecast dates not in historical
            historical_dates = {row['date'] for row in combined_data}
            for row in forecast_data:
                if row['date'] not in historical_dates:
                    combined_data.append(row)

    # Sort by date
    combined_data.sort(key=lambda x: x['date'])

    # Write combined
    if combined_data:
        with open(combined_path, 'w', newline='') as f:
            fieldnames = combined_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_data)

        print(f"✅ Combined data saved to {combined_path}")
        print(f"   Total records: {len(combined_data)}\n")

    return combined_path

def main():
    print("="*70)
    print("🔮 CAPACITY FORECAST GENERATOR")
    print("="*70)
    print()

    # Fetch tasks
    tasks = get_upcoming_tasks()

    # Generate forecast (next 60 days)
    daily_capacity = generate_forecast(tasks, days_forward=60)

    # Save forecast
    forecast_path = "Reports/capacity_forecast.csv"
    save_forecast_csv(daily_capacity, forecast_path)

    # Combine with historical
    combined_path = combine_historical_and_forecast()

    print("="*70)
    print("✅ FORECAST GENERATION COMPLETE!")
    print("="*70)
    print()
    print(f"📁 Files created:")
    print(f"   - {forecast_path}")
    print(f"   - {combined_path}")
    print()
    print("💡 Open capacity_timeline.html and it will now show both:")
    print("   • Historical capacity (backward looking)")
    print("   • Projected capacity (forward looking)")
    print()

if __name__ == "__main__":
    main()
