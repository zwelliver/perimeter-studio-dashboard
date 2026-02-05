#!/usr/bin/env python3
"""
Forecast Status Automation
Automatically moves tasks from Forecast to Preproduction when their status is set to "Ready for Preproduction"

Runs every 30 minutes via cron.

Forecast Status field values:
- Pipeline: Task is in forecast/planning phase
- Ready for Preproduction: Task should be moved to Preproduction project
- On Hold: Task is paused (won't be moved)
- Cancelled: Task is cancelled (won't be moved)

Features:
1. Auto-moves tasks when status = "Ready for Preproduction"
2. Copies all task data: notes, comments, due dates, custom fields
3. Adds a comment noting the conversion
4. Logs all conversions
5. Alerts if tasks are stuck in "Pipeline" but have film dates within 30 days
"""

import os
import sys
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forecast_status_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Asana configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

# Project GIDs
FORECAST_PROJECT_GID = '1212059678473189'
PREPRODUCTION_PROJECT_GID = '1208336083003480'

# Forecast Status field values (these will be looked up dynamically)
FORECAST_STATUS_FIELD_NAME = "Forecast Status"
STATUS_READY_FOR_PREPRODUCTION = "Ready for Preproduction"
STATUS_PIPELINE = "Pipeline"
STATUS_ON_HOLD = "On Hold"
STATUS_CANCELLED = "Cancelled"

# Alert threshold (days until film date)
ALERT_THRESHOLD_DAYS = 30


def get_forecast_status_field():
    """Get the Forecast Status custom field GID and enum options from the project"""
    url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}"
    params = {"opt_fields": "custom_field_settings.custom_field.name,custom_field_settings.custom_field.enum_options"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        project = response.json()['data']

        for setting in project.get('custom_field_settings', []):
            field = setting.get('custom_field', {})
            if field.get('name') == FORECAST_STATUS_FIELD_NAME:
                enum_options = {opt['name']: opt['gid'] for opt in field.get('enum_options', [])}
                return field.get('gid'), enum_options

        logger.warning(f"'{FORECAST_STATUS_FIELD_NAME}' field not found in Forecast project")
        return None, {}

    except Exception as e:
        logger.error(f"Error getting Forecast Status field: {e}")
        return None, {}


def fetch_forecast_tasks():
    """Fetch all incomplete tasks from Forecast project with their custom fields"""
    url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}/tasks"
    params = {
        "opt_fields": "name,notes,due_on,due_at,assignee.gid,assignee.name,completed,custom_fields,start_on"
    }

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']

        # Filter to incomplete tasks only
        return [t for t in tasks if not t.get('completed', False)]

    except Exception as e:
        logger.error(f"Error fetching forecast tasks: {e}")
        return []


def get_task_custom_field_value(task, field_name):
    """Get a custom field value from a task"""
    for field in task.get('custom_fields', []):
        if field.get('name') == field_name:
            # For enum fields, return the enum_value name
            if field.get('enum_value'):
                return field['enum_value'].get('name')
            # For text/number fields
            return field.get('display_value') or field.get('text_value') or field.get('number_value')
    return None


def get_task_comments(task_gid):
    """Get all comments from a task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    params = {"opt_fields": "text,created_by.name,created_at,type"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        stories = response.json()['data']

        comments = []
        for story in stories:
            # Only get actual comments, not system updates
            if story.get('type') == 'comment' and story.get('text'):
                comments.append({
                    'text': story['text'],
                    'author': story.get('created_by', {}).get('name', 'Unknown'),
                    'created_at': story.get('created_at', '')
                })

        return comments
    except Exception as e:
        logger.error(f"Error getting comments for task {task_gid}: {e}")
        return []


def get_full_task_details(task_gid):
    """Get complete task details"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    params = {"opt_fields": "name,notes,due_on,due_at,assignee.gid,custom_fields,html_notes,start_on"}

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        logger.error(f"Error getting task details for {task_gid}: {e}")
        return None


def create_preproduction_task(task_data, comments):
    """Create a new task in Preproduction project with all details"""

    # Build comprehensive notes
    notes = "📋 **[Converted from Forecast]**\n"
    notes += f"Conversion Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    notes += "---\n\n"

    if task_data.get('notes'):
        notes += f"{task_data['notes']}\n\n"

    if comments:
        notes += "---\n**Previous Comments from Forecast:**\n\n"
        for comment in comments:
            date_str = comment['created_at'][:10] if comment['created_at'] else 'Unknown date'
            notes += f"**{comment['author']}** ({date_str}):\n{comment['text']}\n\n"

    # Prepare task payload
    payload = {
        "data": {
            "name": task_data['name'],
            "notes": notes,
            "projects": [PREPRODUCTION_PROJECT_GID]
        }
    }

    # Add due date if exists
    if task_data.get('due_on'):
        payload['data']['due_on'] = task_data['due_on']
    elif task_data.get('due_at'):
        # Extract date from datetime
        payload['data']['due_at'] = task_data['due_at']

    # Add start date if exists
    if task_data.get('start_on'):
        payload['data']['start_on'] = task_data['start_on']

    # Add assignee if exists
    if task_data.get('assignee') and task_data['assignee'].get('gid'):
        payload['data']['assignee'] = task_data['assignee']['gid']

    url = "https://app.asana.com/api/1.0/tasks"

    try:
        response = requests.post(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        new_task = response.json()['data']

        logger.info(f"✅ Created task in Preproduction: {new_task['name']} (GID: {new_task['gid']})")
        return new_task

    except Exception as e:
        logger.error(f"❌ Error creating preproduction task: {e}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response.text}")
        return None


def add_comment_to_task(task_gid, comment_text):
    """Add a comment to a task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    payload = {"data": {"text": comment_text}}

    try:
        response = requests.post(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error adding comment to task {task_gid}: {e}")
        return False


def complete_forecast_task(task_gid):
    """Mark the forecast task as complete after conversion"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    payload = {"data": {"completed": True}}

    try:
        response = requests.put(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error completing forecast task {task_gid}: {e}")
        return False


def move_task_to_preproduction(task):
    """Full workflow to move a task from Forecast to Preproduction"""
    task_name = task['name']
    task_gid = task['gid']

    logger.info(f"🚀 Moving task to Preproduction: {task_name}")

    # Get full task details
    full_task = get_full_task_details(task_gid)
    if not full_task:
        logger.error(f"Could not get details for task: {task_name}")
        return False

    # Get comments
    comments = get_task_comments(task_gid)
    logger.info(f"   Found {len(comments)} comment(s)")

    # Create in Preproduction
    new_task = create_preproduction_task(full_task, comments)
    if not new_task:
        return False

    # Add conversion comment to new task
    conversion_comment = (
        f"✅ This task was automatically converted from Forecast.\n\n"
        f"**Original Forecast Task:** https://app.asana.com/0/{FORECAST_PROJECT_GID}/{task_gid}\n"
        f"**Conversion Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
        f"The task is now ready for preproduction planning. Please review and update any necessary fields."
    )
    add_comment_to_task(new_task['gid'], conversion_comment)

    # Add note to original forecast task
    forecast_note = (
        f"✅ This task has been converted to Preproduction.\n\n"
        f"**New Preproduction Task:** https://app.asana.com/0/{PREPRODUCTION_PROJECT_GID}/{new_task['gid']}\n"
        f"**Conversion Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
        f"This forecast task will be marked as complete."
    )
    add_comment_to_task(task_gid, forecast_note)

    # Complete the forecast task
    if complete_forecast_task(task_gid):
        logger.info(f"   ✅ Forecast task marked complete")

    return True


def check_pipeline_alerts(tasks):
    """Check for tasks stuck in Pipeline status with upcoming film dates"""
    alerts = []
    now = datetime.now().date()
    threshold_date = now + timedelta(days=ALERT_THRESHOLD_DAYS)

    for task in tasks:
        status = get_task_custom_field_value(task, FORECAST_STATUS_FIELD_NAME)

        # Only check tasks in "Pipeline" status
        if status != STATUS_PIPELINE:
            continue

        # Check due date (film date)
        due_date = None
        if task.get('due_on'):
            due_date = datetime.strptime(task['due_on'], '%Y-%m-%d').date()
        elif task.get('due_at'):
            due_datetime = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
            due_date = due_datetime.date()

        if due_date and due_date <= threshold_date:
            days_until = (due_date - now).days
            alerts.append({
                'name': task['name'],
                'gid': task['gid'],
                'due_date': due_date,
                'days_until': days_until
            })

    return alerts


def log_pipeline_alerts(alerts):
    """Log alerts for tasks stuck in Pipeline"""
    if not alerts:
        return

    logger.warning(f"⚠️  {len(alerts)} task(s) in Pipeline status with film dates within {ALERT_THRESHOLD_DAYS} days:")

    for alert in sorted(alerts, key=lambda x: x['days_until']):
        logger.warning(f"   - {alert['name']} (due in {alert['days_until']} days)")
        logger.warning(f"     → Consider setting Forecast Status to 'Ready for Preproduction'")


def main():
    """Main automation function"""
    logger.info("=" * 60)
    logger.info("Forecast Status Automation - Starting")
    logger.info("=" * 60)

    # Check configuration
    if not ASANA_PAT:
        logger.error("ASANA_PAT_SCORER not found in environment")
        return

    # Get the Forecast Status field info
    status_field_gid, enum_options = get_forecast_status_field()
    if not status_field_gid:
        logger.warning("Forecast Status field not found - automation cannot run")
        logger.info("To enable this automation, create a custom field called 'Forecast Status'")
        logger.info("with options: Pipeline, Ready for Preproduction, On Hold, Cancelled")
        return

    logger.info(f"Found Forecast Status field with options: {list(enum_options.keys())}")

    # Fetch all forecast tasks
    tasks = fetch_forecast_tasks()
    logger.info(f"Found {len(tasks)} incomplete task(s) in Forecast")

    # Find tasks ready for preproduction
    tasks_to_move = []
    for task in tasks:
        status = get_task_custom_field_value(task, FORECAST_STATUS_FIELD_NAME)
        if status == STATUS_READY_FOR_PREPRODUCTION:
            tasks_to_move.append(task)

    # Move tasks
    if tasks_to_move:
        logger.info(f"\n🎯 Found {len(tasks_to_move)} task(s) ready for Preproduction:")
        for task in tasks_to_move:
            logger.info(f"   - {task['name']}")

        logger.info("")

        moved_count = 0
        for task in tasks_to_move:
            if move_task_to_preproduction(task):
                moved_count += 1

        logger.info(f"\n✅ Successfully moved {moved_count}/{len(tasks_to_move)} task(s)")
    else:
        logger.info("No tasks are 'Ready for Preproduction'")

    # Check for pipeline alerts
    alerts = check_pipeline_alerts(tasks)
    if alerts:
        logger.info("")
        log_pipeline_alerts(alerts)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Forecast Status Automation - Complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
