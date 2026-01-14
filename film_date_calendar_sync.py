#!/usr/bin/env python3
"""
Two-Way Sync: Asana Film Date ←→ Google Calendar
- Asana → Calendar: Creates/updates/deletes calendar events when Film Date is set/changed/cleared
- Calendar → Asana: Updates Film Date when events are rescheduled in Google Calendar
- Conflict Resolution: Most recent change wins (based on modification timestamps)
- Deletion Handling: Calendar event deletion clears Film Date and sets Task Progress to "Needs Scheduling"
"""

import os
import pickle
import json
from datetime import datetime, time as dt_time, timedelta
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

FILM_DATE_FIELD_GID = os.getenv('FILM_DATE_FIELD_GID')
TASK_PROGRESS_FIELD_GID = os.getenv('TASK_PROGRESS_FIELD_GID')
NEEDS_SCHEDULING_OPTION_GID = os.getenv('NEEDS_SCHEDULING_OPTION_GID')

# Google Calendar config
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.pickle'
MAPPING_FILE = 'film_calendar_mapping.json'  # Maps task GID to event info

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

def fetch_tasks_with_film_dates():
    """Fetch all tasks from Asana that have a Film Date set"""
    tasks_with_dates = []

    for project_name, project_gid in ASANA_PROJECTS.items():
        print(f"  Checking {project_name}...", end=' ')

        try:
            response = requests.get(
                f'https://app.asana.com/api/1.0/projects/{project_gid}/tasks',
                headers=ASANA_HEADERS,
                params={
                    'opt_fields': f'gid,name,completed,custom_fields,modified_at'
                }
            )

            if response.status_code == 200:
                tasks = response.json().get('data', [])
                count = 0

                for task in tasks:
                    if task.get('completed'):
                        continue

                    # Extract Film Date (can be date_time or just date)
                    film_datetime = None
                    for field in task.get('custom_fields', []):
                        if field.get('gid') == FILM_DATE_FIELD_GID:
                            date_value = field.get('date_value')
                            if date_value and isinstance(date_value, dict):
                                # Check for date_time first, then fall back to date
                                film_datetime = date_value.get('date_time') or date_value.get('date')
                            break

                    if film_datetime:
                        tasks_with_dates.append({
                            'gid': task['gid'],
                            'name': task['name'],
                            'film_datetime': film_datetime,
                            'project': project_name,
                            'modified_at': task.get('modified_at')
                        })
                        count += 1

                print(f"✓ {count} with film dates")
            else:
                print(f"⚠️ Error: {response.status_code}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

    return tasks_with_dates

def update_asana_film_date(task_gid, new_datetime):
    """Update the Film Date field in Asana"""
    try:
        response = requests.put(
            f'https://app.asana.com/api/1.0/tasks/{task_gid}',
            headers=ASANA_HEADERS,
            json={
                'data': {
                    'custom_fields': {
                        FILM_DATE_FIELD_GID: new_datetime
                    }
                }
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    ⚠️ Error updating Asana: {e}")
        return False

def clear_film_date_and_set_needs_scheduling(task_gid, task_name):
    """Clear Film Date and set Task Progress to 'Needs Scheduling'"""
    try:
        print(f"    Clearing Film Date for: {task_name}")
        response = requests.put(
            f'https://app.asana.com/api/1.0/tasks/{task_gid}',
            headers=ASANA_HEADERS,
            json={
                'data': {
                    'custom_fields': {
                        FILM_DATE_FIELD_GID: None,
                        TASK_PROGRESS_FIELD_GID: NEEDS_SCHEDULING_OPTION_GID
                    }
                }
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    ⚠️ Error clearing film date: {e}")
        return False

def create_or_update_event(service, task, mapping):
    """Create or update a calendar event for a task"""
    task_gid = task['gid']
    event_info = mapping.get(task_gid, {})
    event_id = event_info.get('event_id') if isinstance(event_info, dict) else event_info

    start_datetime = task['film_datetime']

    # Handle both datetime strings (with time) and date strings (date only)
    if 'T' not in start_datetime:
        # Date only - add default time of 9:00 AM
        start_datetime = f"{start_datetime}T09:00:00.000Z"

    start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
    end_dt = start_dt + timedelta(hours=1)
    end_datetime = end_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    event = {
        'summary': f"🎬 {task['name']}",
        'description': f"Filming session for {task['project']} project\n\nAsana Task: https://app.asana.com/0/0/{task_gid}/f",
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'UTC',
        },
        'colorId': '7',  # Peacock (blue/teal) for film dates
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 60},
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
                'start_time': start_datetime
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
                'start_time': start_datetime
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
    print("\n⬅️  Checking for changes in Google Calendar...")

    updates_from_calendar = 0
    deletions_from_calendar = 0

    # Check each mapped event
    for task_gid, event_info in list(mapping.items()):
        if not isinstance(event_info, dict):
            # Old format, skip for now
            continue

        event_id = event_info.get('event_id')
        last_known_time = event_info.get('start_time')

        try:
            # Fetch current event from calendar
            event = service.events().get(
                calendarId=CALENDAR_ID,
                eventId=event_id
            ).execute()

            # Check if event was rescheduled
            current_start = event['start'].get('dateTime')
            if current_start and current_start != last_known_time:
                print(f"    📅 Calendar event rescheduled: {event.get('summary', 'Unknown')}")
                print(f"       Old time: {last_known_time}")
                print(f"       New time: {current_start}")

                # Update Asana with new time
                if update_asana_film_date(task_gid, current_start):
                    print(f"       ✅ Updated Asana Film Date")
                    event_info['start_time'] = current_start
                    mapping[task_gid] = event_info
                    updates_from_calendar += 1

        except HttpError as error:
            if error.resp.status == 410 or error.resp.status == 404:
                # Event was deleted in calendar
                print(f"    🗑️  Calendar event deleted for task: {task_gid}")
                if clear_film_date_and_set_needs_scheduling(task_gid, f"Task {task_gid}"):
                    print(f"       ✅ Cleared Film Date and set to 'Needs Scheduling'")
                    del mapping[task_gid]
                    deletions_from_calendar += 1
            else:
                print(f"    ⚠️ Error checking event {event_id}: {error}")

    if updates_from_calendar > 0:
        print(f"\n📥 Synced {updates_from_calendar} reschedules from Calendar to Asana")
    if deletions_from_calendar > 0:
        print(f"🗑️  Processed {deletions_from_calendar} deletions from Calendar")

    return updates_from_calendar, deletions_from_calendar

def sync_calendar():
    """Main two-way sync function"""
    print("🔄 Two-Way Film Date Calendar Sync\n")
    print("=" * 70)

    # Get calendar service
    print("\n📅 Authenticating with Google Calendar...")
    service = get_calendar_service()
    print("✅ Authenticated\n")

    # Load existing mapping
    mapping = load_mapping()
    print(f"📋 Loaded {len(mapping)} existing mappings\n")

    # STEP 1: Sync FROM Calendar TO Asana (check for calendar changes first)
    calendar_updates, calendar_deletions = sync_from_calendar(service, mapping)

    # STEP 2: Fetch tasks with film dates from Asana
    print("\n🔍 Fetching tasks with Film Dates from Asana...")
    tasks = fetch_tasks_with_film_dates()
    print(f"\n✅ Found {len(tasks)} tasks with Film Dates\n")

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

    # STEP 4: Clean up tasks that no longer have Film Date
    removed_count = 0
    for task_gid, event_info in list(mapping.items()):
        if task_gid not in current_task_gids:
            event_id = event_info.get('event_id') if isinstance(event_info, dict) else event_info
            if delete_event(service, event_id, f"Task {task_gid}"):
                del mapping[task_gid]
                removed_count += 1

    if removed_count > 0:
        print(f"\n🗑️ Removed {removed_count} events for tasks with cleared Film Dates")

    # Save updated mapping
    save_mapping(mapping)

    print("\n" + "=" * 70)
    print("✅ Two-way sync complete!")
    print(f"📊 Total events in calendar: {len(mapping)}")
    print(f"📥 Calendar → Asana updates: {calendar_updates}")
    print(f"📤 Asana → Calendar updates: {asana_updates}")
    print(f"🗑️  Deletions processed: {calendar_deletions + removed_count}")

if __name__ == '__main__':
    try:
        sync_calendar()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
