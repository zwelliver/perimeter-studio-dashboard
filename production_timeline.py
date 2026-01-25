import requests
from requests.exceptions import HTTPError
import json
import datetime
import os
import time
import re
import pickle
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file in the current directory
load_dotenv(".env")

# Asana setup
ASANA_PAT_BACKDROP = os.getenv("ASANA_PAT_BACKDROP")
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT_BACKDROP}", "Content-Type": "application/json"}

# Project IDs and assignee mapping
PROJECTS = {
    "Production": {
        "gid": "1209597979075357",
        "assignee_gid": "1202206953008470",  # Nick Clark
        "assignee_name": "Nick Clark",
        "capacity_limit": 100
    },
    "Post Production": {
        "gid": "1209581743268502",
        "assignee_gid": "1208249805795150",  # Adriel Abella
        "assignee_name": "Adriel Abella",
        "capacity_limit": 100
    }
}

# Team capacity configuration (includes Preproduction for reporting)
TEAM_CAPACITY = {
    "Zach Welliver": {"gid": "1205076276256605", "capacity": 50},
    "Nick Clark": {"gid": "1202206953008470", "capacity": 100},
    "Adriel Abella": {"gid": "1208249805795150", "capacity": 100},
    "John Meyer": {"gid": "1211292436943049", "capacity": 30}
}

# Custom field GID for Percent allocation
PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"

# Preproduction project for capacity tracking
PREPRODUCTION_PROJECT_GID = "1208336083003480"

# Grok API setup (switched from Claude to free up Claude API)
XAI_API_KEY = os.getenv("GROK_API_KEY")
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {
    "Authorization": f"Bearer {XAI_API_KEY}",
    "Content-Type": "application/json"
}
GROK_PROMPT_TIMELINE = """You are a video production timeline optimizer. Create a BRIEF, scannable timeline with ONLY 3-5 critical milestones from today ({{today}}) to due date ({{due_date}}).

RULES:
- Maximum 5 lines total
- Use format: "Mon DD-DD: Action" (e.g., "Nov 18-20: Script & prep")
- Group related tasks into single phases
- Use action verbs (no descriptions or explanations)
- Focus on: Pre-production → Production → Post-production
- Account for complexity and team availability

Return EXACTLY this JSON format with a bulleted list, no additional text:
{{"timeline": "• Nov 18-20: Script & prep\n• Nov 21-22: Film\n• Nov 25-27: Edit & review\n• Nov 28: Deliver"}}"""

# Google Calendar setup
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.pickle'

# Define base directory for state files
BASE_DIR = os.path.expanduser("~/Scripts/StudioProcesses")
PROCESSED_FILE = os.path.join(BASE_DIR, "processed_timeline.txt")

# Load processed tasks
def load_processed_tasks():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# Save processed task
def save_processed_task(gid):
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{gid}\n")

def get_last_run_time(project_gid):
    last_run_file = os.path.join(BASE_DIR, f"timeline_last_run_{project_gid}.txt")
    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as f:
            last_run_str = f.read().strip()
        try:
            return datetime.datetime.fromisoformat(last_run_str)
        except ValueError:
            print(f"Invalid timestamp for {project_gid}, resetting to default")
    return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

def update_last_run_time(project_gid):
    last_run_file = os.path.join(BASE_DIR, f"timeline_last_run_{project_gid}.txt")
    current_time = datetime.datetime.now(datetime.timezone.utc)
    with open(last_run_file, 'w') as f:
        f.write(current_time.isoformat())
    print(f"Updated last run time for {project_gid}: {current_time}")

def get_sync_token(project_gid):
    sync_token_file = os.path.join(BASE_DIR, f"timeline_sync_{project_gid}.txt")
    if os.path.exists(sync_token_file):
        with open(sync_token_file, 'r') as f:
            return f.read().strip()
    return None

def update_sync_token(project_gid, new_token):
    sync_token_file = os.path.join(BASE_DIR, f"timeline_sync_{project_gid}.txt")
    if new_token:
        with open(sync_token_file, 'w') as f:
            f.write(new_token)
        print(f"Updated sync token for {project_gid}")

def fetch_added_gids(project_gid, sync_token):
    events_endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/events"
    added_gids = set()
    params = {"sync": sync_token} if sync_token else {}
    try:
        response = requests.get(events_endpoint, headers=ASANA_HEADERS, params=params)
        if response.status_code == 412:
            print("412 error, retrying without sync token after delay")
            time.sleep(2)
            response = requests.get(events_endpoint, headers=ASANA_HEADERS)
            if response.status_code == 412:
                print("Retry failed with 412")
                response_data = response.json()
                new_sync_token = response_data.get("sync")
                update_sync_token(project_gid, new_sync_token)
                return set()
        response.raise_for_status()
        data = response.json()
        events = data.get("data", [])
        added_gids = {event["resource"]["gid"] for event in events if event.get("action") == "added" and event.get("resource", {}).get("resource_type") == "task"}
        new_sync_token = data.get("sync")
        update_sync_token(project_gid, new_sync_token)
        print(f"Tasks added: {len(added_gids)}")
    except Exception as e:
        print(f"Events Error: {e}")
    return added_gids

def fetch_task_gids(project_gid):
    endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,created_at,modified_at,notes,custom_fields"
    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS)
        response.raise_for_status()
        return [task["gid"] for task in response.json()["data"]]
    except Exception as e:
        print(f"Asana Error (task list): {e}")
        return []

def fetch_task_details(gid):
    endpoint = f"https://app.asana.com/api/1.0/tasks/{gid}?opt_fields=gid,name,created_at,modified_at,notes,custom_fields,assignee"
    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS)
        response.raise_for_status()
        return response.json()["data"]
    except Exception as e:
        print(f"Asana Error (task {gid}): {e}")
        return None

def filter_new_tasks(tasks, added_gids, last_run_time, processed_tasks):
    new_tasks = []
    APPROVAL_FIELD = "Approval"
    VIRTUAL_LOCATION_FIELD = "Virtual Location"
    for task in tasks:
        gid = task["gid"]
        if gid in processed_tasks:
            print(f"Skipping processed task: {task['name']} (GID: {gid})")
            continue
        created_at = datetime.datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
        modified_at = datetime.datetime.fromisoformat(task['modified_at'].replace('Z', '+00:00'))
        custom_fields = {}
        for cf in task["custom_fields"]:
            if isinstance(cf, dict):
                value = cf["enum_value"]["name"] if cf.get("enum_value") else cf.get("text_value")
                custom_fields[cf["name"]] = value
        is_approved = custom_fields.get(APPROVAL_FIELD) == "Approved"
        virtual_location_value = custom_fields.get(VIRTUAL_LOCATION_FIELD) or ""
        has_virtual_location = bool(virtual_location_value.strip() if isinstance(virtual_location_value, str) else False)
        is_newly_added = gid in added_gids
        if (is_newly_added or modified_at > last_run_time or created_at > last_run_time) and is_approved and not has_virtual_location:
            new_tasks.append(task)
            print(f" -> Added as new task for timeline generation")
        else:
            print(f" -> Skipped")
    return new_tasks

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
            print("Calendar authentication required - using credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_availability_summary(service, today_str, due_date_str):
    """Get real availability from Google Calendar by analyzing scheduled events"""

    # Parse dates
    try:
        today = datetime.datetime.strptime(today_str, "%B %d, %Y")
        due_date = datetime.datetime.strptime(due_date_str, "%B %d, %Y")
    except ValueError:
        # If parsing fails, return default
        return "Calendar availability unknown - standard 20 hours/week assumed."

    # Get events from calendar
    time_min = today.isoformat() + 'Z'
    time_max = due_date.isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Categorize events
        film_dates = []
        due_dates = []
        other_events = []

        for event in events:
            summary = event.get('summary', '')

            if summary.startswith('🎬'):
                film_dates.append(event)
            elif summary.startswith('✅ DUE:'):
                due_dates.append(event)
            else:
                # Count other calendar events (meetings, etc)
                other_events.append(event)

        # Calculate business days between today and due date
        total_days = (due_date - today).days
        business_days = total_days * 5 // 7  # Rough estimate

        # Build availability summary
        summary_parts = []
        summary_parts.append(f"Timeline window: {total_days} days (~{business_days} work days)")

        if film_dates:
            summary_parts.append(f"{len(film_dates)} shoots already scheduled")
            # List first few scheduled shoots
            upcoming_shoots = [e.get('summary', '').replace('🎬 ', '') for e in film_dates[:3]]
            if upcoming_shoots:
                summary_parts.append(f"Upcoming: {', '.join(upcoming_shoots)}")

        if due_dates:
            summary_parts.append(f"{len(due_dates)} deadlines in this period")

        if other_events:
            summary_parts.append(f"{len(other_events)} other calendar commitments")

        # Estimate available days
        scheduled_days = len(film_dates) + (len(other_events) // 2)  # Assume other events are half-day
        available_days = business_days - scheduled_days

        if available_days > 0:
            summary_parts.append(f"~{available_days} days available for new work")
        else:
            summary_parts.append("⚠️ Calendar is heavily booked")

        return " | ".join(summary_parts)

    except Exception as e:
        print(f"Error fetching calendar data: {e}")
        return "Calendar check failed - assuming standard availability"

def get_timeline_suggestion(project_details, complexity, availability_summary, today, due_date):
    grok_payload = {
        "model": "grok-4-fast-non-reasoning",  # Grok 4 fast for timeline planning
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": "You are a video production timeline optimizer."},
            {"role": "user", "content": f"{GROK_PROMPT_TIMELINE.replace('{{today}}', today).replace('{{due_date}}', due_date)}\n\nProject details:\n{project_details}\nComplexity: {complexity}\nAvailability: {availability_summary}"}
        ]
    }
    print(f"Debug: Sending Grok payload (length: {len(json.dumps(grok_payload))} chars)")
    timeline_suggestion = f"• Unable to generate timeline\n• Due: {due_date}\n• Complexity: {complexity}"
    for attempt in range(3):
        try:
            response = requests.post(GROK_ENDPOINT, json=grok_payload, headers=GROK_HEADERS, timeout=60)
            print(f"Debug: Grok response status: {response.status_code}")
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            json_content = json_match.group(1) if json_match else content
            result = json.loads(json_content)
            timeline_suggestion = result.get("timeline", timeline_suggestion)
            print(f"Timeline generated successfully: {len(timeline_suggestion)} chars")
            break
        except Exception as e:
            print(f"Grok timeline error (attempt {attempt + 1}): {e}")
            if hasattr(e, 'response'):
                print(f"Debug: API error details: {e.response.text[:200]}")
            time.sleep(2)
    return timeline_suggestion

def get_task_allocation(task):
    """Get the allocation percentage from a task's custom fields (convert from decimal)"""
    custom_fields = task.get('custom_fields', [])
    for cf in custom_fields:
        if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
            value = cf.get('number_value', 0) or 0
            return value * 100  # Convert decimal to percentage
    return 0

def get_current_capacity_for_all():
    """Get current capacity usage for all team members across all projects"""
    capacity_usage = {name: 0 for name in TEAM_CAPACITY.keys()}

    # Check all three projects
    all_project_gids = [PREPRODUCTION_PROJECT_GID] + [p["gid"] for p in PROJECTS.values()]

    for project_gid in all_project_gids:
        endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,custom_fields,completed,assignee"
        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]

            for task in tasks:
                # Skip completed tasks
                if task.get('completed', False):
                    continue

                # Get assignee
                assignee = task.get('assignee')
                if not assignee:
                    continue

                assignee_gid = assignee.get('gid')

                # Find which team member this is
                for member_name, member_info in TEAM_CAPACITY.items():
                    if member_info["gid"] == assignee_gid:
                        allocation = get_task_allocation(task)
                        capacity_usage[member_name] += allocation
                        break
        except Exception as e:
            print(f"Error getting capacity for project {project_gid}: {e}")

    return capacity_usage

def assign_task(task_id, task, assignee_gid, assignee_name, capacity_limit):
    """Assign a task to a specific user and show capacity impact"""

    # Get current assignee (if any)
    current_assignee = task.get('assignee')
    old_assignee_name = None
    if current_assignee:
        old_assignee_gid = current_assignee.get('gid')
        for member_name, member_info in TEAM_CAPACITY.items():
            if member_info["gid"] == old_assignee_gid:
                old_assignee_name = member_name
                break

    # Get task allocation
    allocation = get_task_allocation(task)

    # Get current capacity for all
    capacity_before = get_current_capacity_for_all()

    # Perform assignment
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    try:
        response = requests.put(url, headers=ASANA_HEADERS, json={"data": {"assignee": assignee_gid}})
        response.raise_for_status()

        # Show capacity change
        if old_assignee_name and old_assignee_name != assignee_name:
            old_capacity = capacity_before[old_assignee_name]
            new_old_capacity = old_capacity - allocation
            print(f"  {old_assignee_name}: {old_capacity:.1f}% → {new_old_capacity:.1f}% (freed {allocation:.1f}%)")

        new_capacity = capacity_before[assignee_name] + allocation
        status = "⚠️  OVER" if new_capacity > capacity_limit else "✅"
        print(f"  {assignee_name}: {capacity_before[assignee_name]:.1f}% → {new_capacity:.1f}% (+{allocation:.1f}%) {status}")

        if new_capacity > capacity_limit:
            print(f"  ⚠️  WARNING: {assignee_name} now at {new_capacity:.1f}% (over {capacity_limit}% limit)")

        return True
    except Exception as e:
        print(f"Error assigning task: {e}")
        return False

def post_comment(task_id, comment):
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/stories"
    try:
        requests.post(url, headers=ASANA_HEADERS, json={"data": {"text": comment}})
        print(f"Commented on task {task_id}")
    except Exception as e:
        print(f"Error commenting: {e}")

# Main execution
print("=" * 60)
print("Starting Production Timeline Script - Multi-Project Mode")
print("=" * 60)

# Initialize Google Calendar service for availability checking
print("\n📅 Initializing Google Calendar...")
try:
    calendar_service = get_calendar_service()
    print("✅ Calendar connected\n")
except Exception as e:
    print(f"⚠️  Calendar unavailable ({e}) - will use fallback availability\n")
    calendar_service = None

processed_tasks = load_processed_tasks()

# Process each project
for project_name, project_config in PROJECTS.items():
    project_gid = project_config["gid"]
    assignee_gid = project_config["assignee_gid"]
    assignee_name = project_config["assignee_name"]

    print(f"\n{'='*60}")
    print(f"Processing {project_name} Project (Assignee: {assignee_name})")
    print(f"{'='*60}")

    last_run_time = get_last_run_time(project_gid)
    sync_token = get_sync_token(project_gid)
    update_last_run_time(project_gid)  # Update immediately

    added_gids = fetch_added_gids(project_gid, sync_token)
    task_gids = fetch_task_gids(project_gid)

    # Fetch tasks efficiently
    tasks = []
    for gid in task_gids:
        details = fetch_task_details(gid)
        if details:
            tasks.append(details)

    new_tasks = filter_new_tasks(tasks, added_gids, last_run_time, processed_tasks)
    print(f"Number of tasks to process in {project_name}: {len(new_tasks)}")

    for task in new_tasks:
        task_name = task["name"]
        task_id = task["gid"]
        description = task.get("notes", "No description provided")
        project_details = f"{task_name}. {description}"

        # Assign task to appropriate person based on project (show capacity change)
        print(f"\nAssigning task: {task_name}")
        assign_task(task_id, task, assignee_gid, assignee_name, project_config["capacity_limit"])

        # Only generate timeline for Production project
        if project_name == "Production":
            # Extract due date and complexity
            due_date_match = re.search(r"Date Needed:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", description)
            due_date = due_date_match.group(1) if due_date_match else "Unknown"
            complexity_match = re.search(r"Timeline Urgency:\s*(.*?)(?:\n|$)", description)
            complexity = complexity_match.group(1) if complexity_match else "Standard (4-6 weeks)"
            today = datetime.datetime.now().strftime("%B %d, %Y")

            availability_summary = get_availability_summary(calendar_service, today, due_date) if calendar_service else "Calendar unavailable - assuming standard availability"
            timeline_suggestion = get_timeline_suggestion(project_details, complexity, availability_summary, today, due_date)

            comment = f"📅 **Suggested Timeline** (Due: {due_date})\n\n{timeline_suggestion}\n\n_Auto-generated based on complexity and team availability_"
            post_comment(task_id, comment)

        save_processed_task(task_id)

    # Final update for this project
    update_last_run_time(project_gid)

print(f"\n{'='*60}")
print("FINAL TEAM CAPACITY REPORT")
print(f"{'='*60}")

# Get final capacity for all team members
final_capacity = get_current_capacity_for_all()
for member_name, usage in final_capacity.items():
    limit = TEAM_CAPACITY[member_name]["capacity"]
    status = "⚠️  OVER CAPACITY" if usage > limit else "✅ OK"
    print(f"{member_name:20s} {usage:6.1f}% / {limit:3d}%  {status}")

print(f"{'='*60}")
print("Script Completed")
print(f"{'='*60}")
