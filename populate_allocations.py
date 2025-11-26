#!/usr/bin/env python3
"""
One-time script to populate allocation percentages for all tasks
Replicates video_scorer.py allocation calculation logic
"""

import requests
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv(".env")

ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

# Constants from video_scorer.py
PHASE_MULTIPLIERS = {
    "Preproduction": 0.8,
    "Production": 1.2,
    "Post Production": 2.0,
    "Forecast": 1.0
}

DEFAULT_DURATION_DAYS = 30
PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"

PROJECT_GIDS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}

def extract_video_duration(notes):
    """Extract video duration from notes/description"""
    if not notes:
        return None

    # Look for patterns like "5 min", "10 minutes", "1:30", etc.
    patterns = [
        r'(\d+)\s*min(?:ute)?s?',  # "5 min" or "10 minutes"
        r'(\d+):(\d+)',  # "1:30" format
    ]

    for pattern in patterns:
        match = re.search(pattern, notes, re.IGNORECASE)
        if match:
            if ':' in pattern:
                mins = int(match.group(1)) * 60 + int(match.group(2))
                return mins / 60  # Convert to decimal minutes
            else:
                return int(match.group(1))

    return None

def get_complexity_from_duration(duration_mins):
    """Convert video duration to complexity score (1-12 scale)"""
    if not duration_mins:
        return 5  # Default medium complexity

    if duration_mins < 2:
        return 3  # Simple
    elif duration_mins < 5:
        return 5  # Medium-simple
    elif duration_mins < 10:
        return 7  # Medium
    elif duration_mins < 15:
        return 9  # Medium-complex
    else:
        return 11  # Complex

def calculate_allocation(priority, complexity, project_name, start_date, due_date):
    """Calculate allocation percentage - from video_scorer.py"""
    if not priority or not complexity:
        return 0

    # Get phase multiplier
    phase_multiplier = PHASE_MULTIPLIERS.get(project_name, 1.0)

    # Base calculation
    base = (complexity * 3.5) * phase_multiplier

    # Priority factor (0.5 to 1.0 range for priority 1-12)
    priority_factor = 0.5 + (priority / 24)

    # Calculate duration in weeks
    if start_date and due_date:
        try:
            start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            due = datetime.fromisoformat(due_date) if isinstance(due_date, str) else due_date
            duration_days = max((due - start).days, 1)
            duration_weeks = max(duration_days / 7, 0.5)
        except:
            duration_weeks = 2
    else:
        duration_weeks = 2

    # Calculate raw allocation
    raw_allocation = (base * priority_factor) / duration_weeks

    # Apply floor and cap
    allocation = max(min(raw_allocation, 80.0), 5.0)

    return round(allocation, 1)

def process_all_tasks():
    """Process all tasks and update their allocations"""
    total_updated = 0

    for phase, project_gid in PROJECT_GIDS.items():
        print(f"\nProcessing {phase}...")

        # Fetch all tasks with custom fields
        response = requests.get(
            f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks",
            headers=ASANA_HEADERS,
            params={
                "opt_fields": "name,notes,due_on,start_on,custom_fields.name,custom_fields.number_value,custom_fields.gid"
            }
        )

        if response.status_code != 200:
            print(f"  Error fetching tasks: {response.status_code}")
            continue

        tasks = response.json()["data"]
        print(f"  Found {len(tasks)} tasks")

        for task in tasks:
            # Check if task has a video link (presence indicates it's a video task)
            notes = task.get('notes', '')
            if not notes or ('vimeo.com' not in notes.lower() and 'youtube.com' not in notes.lower() and 'drive.google.com' not in notes.lower()):
                continue  # Skip non-video tasks

            # Extract video duration
            duration = extract_video_duration(notes)

            # Get complexity from duration
            complexity = get_complexity_from_duration(duration)

            # Get priority from custom fields (default to 6 if not set)
            priority = 6
            for cf in task.get('custom_fields', []):
                if cf.get('name') == 'Priority':
                    priority = cf.get('number_value', 6) or 6
                    break

            # Calculate allocation
            allocation = calculate_allocation(
                priority=priority,
                complexity=complexity,
                project_name=phase,
                start_date=task.get('start_on'),
                due_date=task.get('due_on')
            )

            # Update the Percent Allocation custom field
            try:
                update_response = requests.put(
                    f"https://app.asana.com/api/1.0/tasks/{task['gid']}",
                    headers=ASANA_HEADERS,
                    json={
                        "data": {
                            "custom_fields": {
                                PERCENT_ALLOCATION_FIELD_GID: allocation
                            }
                        }
                    }
                )

                if update_response.status_code == 200:
                    total_updated += 1
                    print(f"  ✓ {task['name'][:50]}: {allocation}%")
                else:
                    print(f"  ✗ Failed to update {task['name'][:50]}: {update_response.status_code}")

            except Exception as e:
                print(f"  ✗ Error updating {task['name'][:50]}: {e}")

    print(f"\n✅ Successfully updated {total_updated} tasks")

if __name__ == "__main__":
    print("Populating allocation percentages for all video tasks...")
    process_all_tasks()
    print("\nDone! Now run generate_dashboard.py to see updated heatmap.")
