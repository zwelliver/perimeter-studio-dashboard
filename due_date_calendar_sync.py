#!/usr/bin/env python3
"""
Two-Way Sync: Asana Due Dates ←→ Google Calendar
- Asana → Calendar: Creates/updates/deletes calendar events when due dates are set/changed/cleared
- Calendar → Asana: Updates due dates when events are rescheduled in Google Calendar
- Conflict Resolution: Most recent change wins (based on modification timestamps)
- Event Type: All-day events (cleaner, doesn't block time slots)
"""

import os
import pickle
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

# Google Calendar config
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.pickle'
MAPPING_FILE = 'due_calendar_mapping.json'  # Separate mapping for due dates

def get_calendar_service():
    """Authenticate and return Google Calendar service"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            print("First time setup - Opening browser for authorization...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def load_mapping():
    """Load task GID to calendar event mapping with timestamps"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    """Save task GID to calendar event mapping"""
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)

def fetch_tasks_with_due_dates():
    """Fetch all tasks from Asana that have a due date set"""
    tasks_with_dates = []

    for project_name, project_gid in ASANA_PROJECTS.items():
        print(f"  Checking {project_name}...", end=' ')

        try:
            response = requests.get(
                f'https://app.asana.com/api/1.0/projects/{project_gid}/tasks',
                headers=ASANA_HEADERS,
                params={
                    'opt_fields': 'gid,name,completed,due_on,due_at,modified_at'
                }
            )

            if response.status_code == 200:
                tasks = response.json().get('data', [])
                count = 0

                for task in tasks:
                    if task.get('completed'):
                        continue

                    # Extract due date (can be due_on or due_at)
                    due_date = None
                    if task.get('due_on'):
                        # due_on is a date string (YYYY-MM-DD)
                        due_date = task['due_on']
                    elif task.get('due_at'):
                        # due_at is a datetime, extract just the date
                        due_datetime = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
                        due_date = due_datetime.strftime('%Y-%m-%d')

                    if due_date:
                        tasks_with_dates.append({
                            'gid': task['gid'],
                            'name': task['name'],
                            'due_date': due_date,
                            'project': project_name,
                            'modified_at': task.get('modified_at')
                        })
                        count += 1

                print(f"✓ {count} with due dates")
            else:
                print(f"⚠️ Error: {response.status_code}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

    return tasks_with_dates

def update_asana_due_date(task_gid, new_date):
    """Update the due_on field in Asana (YYYY-MM-DD format)"""
    try:
        response = requests.put(
            f'https://app.asana.com/api/1.0/tasks/{task_gid}',
            headers=ASANA_HEADERS,
            json={
                'data': {
                    'due_on': new_date
                }
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    ⚠️ Error updating Asana: {e}")
        return False

def clear_due_date(task_gid, task_name):
    """Clear due date in Asana"""
    try:
        print(f"    Clearing due date for: {task_name}")
        response = requests.put(
            f'https://app.asana.com/api/1.0/tasks/{task_gid}',
            headers=ASANA_HEADERS,
            json={
                'data': {
                    'due_on': None
                }
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    ⚠️ Error clearing due date: {e}")
        return False

def create_or_update_event(service, task, mapping):
    """Create or update a calendar event for a task's due date"""
    task_gid = task['gid']
    event_info = mapping.get(task_gid, {})
    event_id = event_info.get('event_id') if isinstance(event_info, dict) else event_info

    due_date = task['due_date']  # YYYY-MM-DD format

    # Timed event at 4:00 PM EST (21:00 UTC)
    start_datetime = f"{due_date}T21:00:00.000Z"
    end_datetime = f"{due_date}T22:00:00.000Z"

    event = {
        'summary': f"✅ DUE: {task['name']}",
        'description': f"Deadline for {task['project']} project\\n\\nAsana Task: https://app.asana.com/0/0/{task_gid}/f",
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'UTC',
        },
        'colorId': '11',  # Tomato (red) for due dates
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                {'method': 'popup', 'minutes': 60},  # 1 hour before
            ],
        },
    }

    try:
        if event_id:
            print(f"    Updating: {task['name']}")
            updated_event = service.events().update(
                calendarId=CALENDAR_ID,
                eventId=event_id,
                body=event
            ).execute()
            return {
                'event_id': updated_event['id'],
                'updated_at': updated_event.get('updated'),
                'due_date': due_date
            }
        else:
            print(f"    Creating: {task['name']}")
            created_event = service.events().insert(
                calendarId=CALENDAR_ID,
                body=event
            ).execute()
            return {
                'event_id': created_event['id'],
                'updated_at': created_event.get('updated'),
                'due_date': due_date
            }

    except HttpError as error:
        print(f"    ⚠️ Error: {error}")
        return None

def delete_event(service, event_id, task_name):
    """Delete a calendar event"""
    try:
        print(f"    Deleting: {task_name}")
        service.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event_id
        ).execute()
        return True
    except HttpError as error:
        if error.resp.status == 410 or error.resp.status == 404:
            # Event already deleted
            return True
        print(f"    ⚠️ Error deleting: {error}")
        return False

def sync_from_calendar(service, mapping):
    """Sync changes FROM Google Calendar TO Asana"""
    print("\\n⬅️  Checking for changes in Google Calendar...")

    updates_from_calendar = 0
    deletions_from_calendar = 0

    # Check each mapped event
    for task_gid, event_info in list(mapping.items()):
        if not isinstance(event_info, dict):
            # Old format, skip for now
            continue

        event_id = event_info.get('event_id')
        last_known_date = event_info.get('due_date')

        try:
            # Fetch current event from calendar
            event = service.events().get(
                calendarId=CALENDAR_ID,
                eventId=event_id
            ).execute()

            # Check if event was rescheduled (timed events use 'dateTime')
            current_datetime = event['start'].get('dateTime')
            if current_datetime:
                # Extract just the date portion (YYYY-MM-DD)
                current_date = current_datetime.split('T')[0]

                if current_date != last_known_date:
                    print(f"    📅 Calendar event rescheduled: {event.get('summary', 'Unknown')}")
                    print(f"       Old date: {last_known_date}")
                    print(f"       New date: {current_date}")

                    # Update Asana with new date
                    if update_asana_due_date(task_gid, current_date):
                        print(f"       ✅ Updated Asana due date")
                        event_info['due_date'] = current_date
                        mapping[task_gid] = event_info
                        updates_from_calendar += 1

        except HttpError as error:
            if error.resp.status == 410 or error.resp.status == 404:
                # Event was deleted in calendar
                print(f"    🗑️  Calendar event deleted for task: {task_gid}")
                if clear_due_date(task_gid, f"Task {task_gid}"):
                    print(f"       ✅ Cleared due date in Asana")
                    del mapping[task_gid]
                    deletions_from_calendar += 1
            else:
                print(f"    ⚠️ Error checking event {event_id}: {error}")

    if updates_from_calendar > 0:
        print(f"\\n📥 Synced {updates_from_calendar} reschedules from Calendar to Asana")
    if deletions_from_calendar > 0:
        print(f"🗑️  Processed {deletions_from_calendar} deletions from Calendar")

    return updates_from_calendar, deletions_from_calendar

def sync_calendar():
    """Main two-way sync function"""
    print("🔄 Two-Way Due Date Calendar Sync\\n")
    print("=" * 70)

    # Get calendar service
    print("\\n📅 Authenticating with Google Calendar...")
    service = get_calendar_service()
    print("✅ Authenticated\\n")

    # Load existing mapping
    mapping = load_mapping()
    print(f"📋 Loaded {len(mapping)} existing mappings\\n")

    # STEP 1: Sync FROM Calendar TO Asana (check for calendar changes first)
    calendar_updates, calendar_deletions = sync_from_calendar(service, mapping)

    # STEP 2: Fetch tasks with due dates from Asana
    print("\\n🔍 Fetching tasks with due dates from Asana...")
    tasks = fetch_tasks_with_due_dates()
    print(f"\\n✅ Found {len(tasks)} tasks with due dates\\n")

    # STEP 3: Sync FROM Asana TO Calendar
    print("➡️  Syncing from Asana to Google Calendar...")
    current_task_gids = set()
    asana_updates = 0

    for task in tasks:
        current_task_gids.add(task['gid'])
        event_info = create_or_update_event(service, task, mapping)
        if event_info:
            mapping[task['gid']] = event_info
            asana_updates += 1

    print()

    # STEP 4: Clean up tasks that no longer have due dates
    removed_count = 0
    for task_gid, event_info in list(mapping.items()):
        if task_gid not in current_task_gids:
            event_id = event_info.get('event_id') if isinstance(event_info, dict) else event_info
            if delete_event(service, event_id, f"Task {task_gid}"):
                del mapping[task_gid]
                removed_count += 1

    if removed_count > 0:
        print(f"\\n🗑️ Removed {removed_count} events for tasks with cleared due dates")

    # Save updated mapping
    save_mapping(mapping)

    print("\\n" + "=" * 70)
    print("✅ Two-way due date sync complete!")
    print(f"📊 Total events in calendar: {len(mapping)}")
    print(f"📥 Calendar → Asana updates: {calendar_updates}")
    print(f"📤 Asana → Calendar updates: {asana_updates}")
    print(f"🗑️  Deletions processed: {calendar_deletions + removed_count}")

if __name__ == '__main__':
    try:
        sync_calendar()
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
