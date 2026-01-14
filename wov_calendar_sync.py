#!/usr/bin/env python3
"""
Weekly Opportunity Video (WOV) Calendar → Asana Automation
Monitors Google Calendar for WOV events and creates Asana tasks automatically
"""

import os
import pickle
import json
import datetime
import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment variables
load_dotenv(".env")

# Google Calendar setup
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.pickle'

# Asana setup
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
PRODUCTION_PROJECT_GID = "1209597979075357"

# Custom field GIDs
FILM_DATE_FIELD_GID = "1212211613150378"  # Film Date custom field (workspace-level)
START_DATE_FIELD_GID = "1211967927674488"  # Start Date
TASK_PROGRESS_FIELD_GID = "1209598240843051"  # Task Progress (enum)
APPROVAL_FIELD_GID = "1209632867555289"  # Approval (enum)
VIRTUAL_LOCATION_FIELD_GID = "1209661703587753"  # Virtual Location (text)
TYPE_FIELD_GID = "1209581743268525"  # Type (enum)
CATEGORY_FIELD_GID = "1211901611025610"  # Category (enum)

# Enum option GIDs for WOV tasks
TASK_PROGRESS_SCHEDULED_GID = "1209598240843053"  # "Scheduled"
APPROVAL_APPROVED_GID = "1209632867555292"  # "Approved"
TYPE_ENRICHING_GID = "1209581744608311"  # "Enriching"
CATEGORY_COMMUNICATIONS_GID = "1211901611025612"  # "Communications"

ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

# Studio team members to exclude when finding talent
STUDIO_TEAM_EMAILS = [
    "comstudio@perimeter.org",
    "perimetercomstudio@gmail.com",
    "zachw@perimeter.org",
    "zach.welliver@perimeter.org",
    "nickc@perimeter.org",
    "nick.clark@perimeter.org",
    "adriela@perimeter.org",
    "adriel.abella@perimeter.org",
    "johnm@perimeter.org",
    "john.meyer@perimeter.org",
    "eleanorp@perimeter.org",
    "eleanor.pepper@perimeter.org",
    # Add more studio team emails as needed
]

# Mapping file to track processed events
MAPPING_FILE = os.path.expanduser("~/Scripts/StudioProcesses/wov_calendar_mapping.json")


def get_calendar_service():
    """Authenticate and return Google Calendar service"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def load_mapping():
    """Load the mapping of calendar events to Asana tasks"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_mapping(mapping):
    """Save the mapping of calendar events to Asana tasks"""
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)


def extract_talent_name(event):
    """Extract talent name from event attendees"""
    attendees = event.get('attendees', [])

    for attendee in attendees:
        email = attendee.get('email', '').lower()
        display_name = attendee.get('displayName', '')

        # Skip studio team members
        if email in [e.lower() for e in STUDIO_TEAM_EMAILS]:
            continue

        # Found talent!
        if display_name:
            return display_name
        else:
            # Extract name from email if no display name
            return email.split('@')[0].replace('.', ' ').title()

    # No external attendee found
    return "Unknown Talent"


def calculate_due_date(film_date):
    """Calculate due date: Thursday 10am before the Sunday it's shown"""
    # Find the next Sunday after filming (the show date)
    days_until_sunday = (6 - film_date.weekday()) % 7
    if days_until_sunday == 0:  # If film date IS Sunday, use next Sunday
        days_until_sunday = 7
    show_sunday = film_date + datetime.timedelta(days=days_until_sunday)

    # Thursday before that Sunday (3 days before)
    due_thursday = show_sunday - datetime.timedelta(days=3)

    # Set time to 10am EST (which is 15:00 UTC in winter, 14:00 UTC in summer)
    # For simplicity, using 15:00 UTC
    due_datetime = due_thursday.replace(hour=10, minute=0, second=0, microsecond=0)

    return due_datetime


def check_existing_asana_task(talent_name, event_date_str):
    """Check if a WOV task already exists for this talent and date"""
    try:
        # Search for tasks in Production project with matching name pattern
        response = requests.get(
            f"https://app.asana.com/api/1.0/projects/{PRODUCTION_PROJECT_GID}/tasks",
            headers=ASANA_HEADERS,
            params={
                "opt_fields": "gid,name,custom_fields",
                "completed_since": "now"  # Only get incomplete tasks
            }
        )
        response.raise_for_status()
        tasks = response.json().get("data", [])

        # Check for existing WOV task with this talent name and film date
        for task in tasks:
            task_name = task.get("name", "")

            # Check if task name matches "WOV - {talent_name}"
            if task_name == f"WOV - {talent_name}":
                # Check if film date matches
                for field in task.get("custom_fields", []):
                    if field.get("gid") == FILM_DATE_FIELD_GID:
                        date_value = field.get("date_value")
                        if date_value and isinstance(date_value, dict):
                            task_film_date = date_value.get("date")
                            if task_film_date == event_date_str:
                                print(f"   ⚠️  Task already exists: {task_name} (GID: {task['gid']}) with film date {event_date_str}")
                                return task["gid"]

        return None
    except Exception as e:
        print(f"   ⚠️  Error checking existing tasks: {e}")
        return None


def create_asana_task(event_id, talent_name, event_date, event):
    """Create Asana task in Production project"""

    # Parse film date from event
    if 'dateTime' in event['start']:
        film_dt = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
        formatted_film_date = film_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        film_date_str = film_dt.strftime("%Y-%m-%d")
        film_datetime_str = film_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        # All-day event
        film_dt = datetime.datetime.strptime(event['start']['date'], "%Y-%m-%d")
        formatted_film_date = film_dt.strftime("%A, %B %d, %Y")
        film_date_str = event['start']['date']
        film_datetime_str = None

    # Calculate due date (Thursday 10am before Sunday it's shown)
    due_dt = calculate_due_date(film_dt)
    due_date_str = due_dt.strftime("%Y-%m-%d")
    formatted_due_date = due_dt.strftime("%A, %B %d at 10:00 AM")

    task_name = f"WOV - {talent_name}"

    task_description = f"""Weekly Opportunity Video with {talent_name}

🎬 **Film Date:** {formatted_film_date}
📅 **Due Date:** {formatted_due_date} (ready for Sunday service)

This task was automatically created from the calendar event.

**Calendar Event:** {event.get('summary', 'WOV')}
**Event ID:** {event_id}
"""

    # Create Film Date custom field value (date/time picker requires object format)
    film_date_value = {
        "date": film_date_str,
        "datetime": film_datetime_str
    }

    # Create Start Date custom field value (same as film date)
    start_date_value = {
        "date": film_date_str,
        "datetime": film_datetime_str
    }

    # Create task payload with all custom fields
    task_data = {
        "data": {
            "name": task_name,
            "notes": task_description,
            "projects": [PRODUCTION_PROJECT_GID],
            "due_on": due_date_str,
            "custom_fields": {
                FILM_DATE_FIELD_GID: film_date_value,
                START_DATE_FIELD_GID: start_date_value,
                TASK_PROGRESS_FIELD_GID: TASK_PROGRESS_SCHEDULED_GID,
                APPROVAL_FIELD_GID: APPROVAL_APPROVED_GID,
                VIRTUAL_LOCATION_FIELD_GID: "WOV Set",
                TYPE_FIELD_GID: TYPE_ENRICHING_GID,
                CATEGORY_FIELD_GID: CATEGORY_COMMUNICATIONS_GID
            }
        }
    }

    try:
        response = requests.post(
            "https://app.asana.com/api/1.0/tasks",
            headers=ASANA_HEADERS,
            json=task_data
        )
        response.raise_for_status()
        task_gid = response.json()["data"]["gid"]
        print(f"✅ Created task: {task_name} (GID: {task_gid})")
        return task_gid
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error creating Asana task: {e}")
        print(f"   Response body: {response.text}")
        print(f"   Task data sent: {json.dumps(task_data, indent=2)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error creating Asana task: {e}")
        return None


def sync_wov_events():
    """Main sync function"""
    print("=" * 70)
    print(f"WOV CALENDAR SYNC - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Get calendar service
    service = get_calendar_service()

    # Load existing mapping
    mapping = load_mapping()

    # Search for WOV events in the next 3 months
    now = datetime.datetime.now(datetime.UTC)
    time_max = now + datetime.timedelta(days=90)

    # Format timestamps for Google Calendar API (needs Z suffix without timezone offset)
    time_min_str = now.replace(tzinfo=None).isoformat() + 'Z'
    time_max_str = time_max.replace(tzinfo=None).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min_str,
        timeMax=time_max_str,
        q="WOV",  # Search for events with "WOV" in title
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Filter out auto-generated calendar events from due_date_calendar_sync and film_date_calendar_sync
    # These have "✅ DUE:" or "✅ FILM:" prefixes and create a feedback loop
    filtered_events = []
    for event in events:
        summary = event.get('summary', '')
        if not (summary.startswith('✅ DUE:') or summary.startswith('✅ FILM:')):
            filtered_events.append(event)

    events = filtered_events

    print(f"\n📅 Found {len(events)} WOV event(s) in the next 90 days\n")

    new_tasks_created = 0

    for event in events:
        event_id = event['id']
        event_summary = event.get('summary', 'Untitled')

        # Extract talent name and date first
        talent_name = extract_talent_name(event)

        # Get event date
        if 'dateTime' in event['start']:
            event_date_str = event['start']['dateTime'][:10]
        else:
            event_date_str = event['start']['date']

        print(f"🎬 Processing: {event_summary}")
        print(f"   Talent: {talent_name}")
        print(f"   Date: {event_date_str}")

        # FIRST: Check if we already have this event ID mapped
        if event_id in mapping:
            print(f"   ⏭️  Skipping: Event ID already in mapping")
            print()
            continue

        # SECOND: Check if a task already exists in Asana with this talent+date
        existing_task_gid = check_existing_asana_task(talent_name, event_date_str)
        if existing_task_gid:
            # Task exists - update mapping to point to it
            mapping[event_id] = {
                "task_gid": existing_task_gid,
                "talent_name": talent_name,
                "event_date": event_date_str,
                "created_at": datetime.datetime.now().isoformat(),
                "linked_existing": True
            }
            print(f"   ⏭️  Skipping: Linked to existing task (no duplicate created)")
            print()
            continue

        # No existing task found - create a new one
        task_gid = create_asana_task(event_id, talent_name, event_date_str, event)

        if task_gid:
            # Store mapping
            mapping[event_id] = {
                "task_gid": task_gid,
                "talent_name": talent_name,
                "event_date": event_date_str,
                "created_at": datetime.datetime.now().isoformat()
            }
            new_tasks_created += 1

        print()

    # Save mapping
    save_mapping(mapping)

    print("=" * 70)
    print(f"✅ Sync complete: {new_tasks_created} new task(s) created")
    print("=" * 70)


if __name__ == "__main__":
    sync_wov_events()
