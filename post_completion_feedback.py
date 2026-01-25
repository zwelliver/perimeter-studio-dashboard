#!/usr/bin/env python3
"""
Post-Completion Feedback Collection
Automatically posts completion summary and effort feedback request when tasks are completed in Post Production.

Runs every 15 minutes via cron (can be integrated into video_scorer.py).

Features:
1. Detects newly completed tasks in Post Production
2. Calculates actual time metrics (start to completion)
3. Compares estimated vs actual allocation
4. Posts AI-generated completion summary as a comment
5. Includes effort feedback prompt for subjective input
6. Tracks feedback-posted tasks to avoid duplicates
"""

import os
import sys
import json
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
        logging.FileHandler('post_completion_feedback.log'),
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

# Grok API configuration (switched back to Grok to free up Claude API for clawdbot)
XAI_API_KEY = os.getenv("GROK_API_KEY")
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {
    "Authorization": f"Bearer {XAI_API_KEY}",
    "Content-Type": "application/json"
}
GROK_MODEL = "grok-4-fast-non-reasoning"  # Grok 4 fast

# Project GIDs
POST_PRODUCTION_PROJECT_GID = '1209581743268502'
PRODUCTION_PROJECT_GID = '1209597979075357'
PREPRODUCTION_PROJECT_GID = '1208336083003480'

# Track which tasks have received feedback (persistent file)
FEEDBACK_TRACKING_FILE = 'feedback_posted_tasks.json'

# Recipients who should receive feedback notification
FEEDBACK_RECIPIENT = "Zach"  # Will be notified via task comment @mention


def load_feedback_tracking():
    """Load the set of task GIDs that have already received feedback"""
    try:
        if os.path.exists(FEEDBACK_TRACKING_FILE):
            with open(FEEDBACK_TRACKING_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        logger.error(f"Error loading feedback tracking: {e}")
    return set()


def save_feedback_tracking(task_gids):
    """Save the set of task GIDs that have received feedback"""
    try:
        with open(FEEDBACK_TRACKING_FILE, 'w') as f:
            json.dump(list(task_gids), f)
    except Exception as e:
        logger.error(f"Error saving feedback tracking: {e}")


def fetch_recently_completed_tasks():
    """Fetch tasks completed in the last 7 days from Post Production"""
    url = f"https://app.asana.com/api/1.0/projects/{POST_PRODUCTION_PROJECT_GID}/tasks"
    params = {
        "opt_fields": "name,completed,completed_at,created_at,due_on,start_on,notes,assignee.name,custom_fields"
    }

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']

        # Filter to completed tasks from the last 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        completed_tasks = []

        for task in tasks:
            if task.get('completed') and task.get('completed_at'):
                completed_at = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                if completed_at.replace(tzinfo=None) >= cutoff_date:
                    completed_tasks.append(task)

        return completed_tasks

    except Exception as e:
        logger.error(f"Error fetching completed tasks: {e}")
        return []


def get_task_custom_field_value(task, field_name):
    """Get a custom field value from a task"""
    for field in task.get('custom_fields', []):
        if field.get('name') == field_name:
            if field.get('enum_value'):
                return field['enum_value'].get('name')
            return field.get('display_value') or field.get('text_value') or field.get('number_value')
    return None


def calculate_time_metrics(task):
    """Calculate time-based metrics for the task"""
    metrics = {}

    # Get key dates
    created_at = task.get('created_at')
    completed_at = task.get('completed_at')
    due_on = task.get('due_on')
    start_on = task.get('start_on')

    if created_at:
        metrics['created_at'] = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

    if completed_at:
        metrics['completed_at'] = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))

    if due_on:
        metrics['due_date'] = datetime.strptime(due_on, '%Y-%m-%d')

    if start_on:
        metrics['start_date'] = datetime.strptime(start_on, '%Y-%m-%d')

    # Calculate total days from creation to completion
    if 'created_at' in metrics and 'completed_at' in metrics:
        delta = metrics['completed_at'] - metrics['created_at']
        metrics['total_days'] = delta.days

    # Calculate days from start date to completion (if start date exists)
    if 'start_date' in metrics and 'completed_at' in metrics:
        delta = metrics['completed_at'].replace(tzinfo=None) - metrics['start_date']
        metrics['active_days'] = delta.days

    # Calculate on-time status
    if 'due_date' in metrics and 'completed_at' in metrics:
        due_datetime = metrics['due_date']
        completed_datetime = metrics['completed_at'].replace(tzinfo=None)

        days_variance = (completed_datetime.date() - due_datetime.date()).days
        metrics['days_variance'] = days_variance

        if days_variance <= 0:
            metrics['delivery_status'] = 'On Time'
        elif days_variance <= 2:
            metrics['delivery_status'] = 'Slightly Late'
        else:
            metrics['delivery_status'] = 'Late'

    return metrics


def get_allocation_data(task):
    """Get estimated and actual allocation from custom fields"""
    estimated = get_task_custom_field_value(task, '% Allocation')
    actual = get_task_custom_field_value(task, 'Actual Allocation')

    return {
        'estimated_allocation': float(estimated) if estimated else None,
        'actual_allocation': float(actual) if actual else None
    }


def generate_completion_summary_claude(task, metrics, allocation):
    """Use Grok to generate a completion summary"""
    if not XAI_API_KEY:
        return generate_fallback_summary(task, metrics, allocation)

    task_name = task['name']
    task_notes = task.get('notes', '')[:500]  # Truncate long notes
    category = get_task_custom_field_value(task, 'Category') or 'Unknown'
    task_type = get_task_custom_field_value(task, 'Type') or 'Unknown'

    prompt = f"""Generate a brief, friendly completion summary for a video production task.

Task Details:
- Name: {task_name}
- Category: {category}
- Type: {task_type}
- Notes: {task_notes}

Time Metrics:
- Total days from creation to completion: {metrics.get('total_days', 'N/A')}
- Active work days (from start date): {metrics.get('active_days', 'N/A')}
- Delivery status: {metrics.get('delivery_status', 'N/A')}
- Days variance from due date: {metrics.get('days_variance', 'N/A')}

Allocation:
- Estimated allocation: {allocation.get('estimated_allocation', 'N/A')}%
- Actual allocation: {allocation.get('actual_allocation', 'N/A')}%

Write a 2-3 sentence completion summary that:
1. Celebrates the completion
2. Notes key metrics (days, on-time status)
3. Compares estimated vs actual allocation if available
4. Keeps a positive, team-friendly tone

Keep it concise and actionable. End with asking for feedback on effort level."""

    try:
        payload = {
            "model": GROK_MODEL,
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant for a video production team. Generate brief, friendly task completion summaries."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(GROK_ENDPOINT, headers=GROK_HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content'].strip()

    except Exception as e:
        logger.error(f"Error generating summary with Grok: {e}")
        return generate_fallback_summary(task, metrics, allocation)


def generate_fallback_summary(task, metrics, allocation):
    """Generate a simple completion summary without AI"""
    task_name = task['name']

    summary = f"✅ **{task_name}** has been completed!\n\n"

    # Time metrics
    if metrics.get('total_days') is not None:
        summary += f"📅 **Total time:** {metrics['total_days']} days from creation to completion\n"

    if metrics.get('active_days') is not None:
        summary += f"⏱️ **Active work time:** {metrics['active_days']} days\n"

    if metrics.get('delivery_status'):
        status_emoji = "🎯" if metrics['delivery_status'] == 'On Time' else "⚠️"
        summary += f"{status_emoji} **Delivery:** {metrics['delivery_status']}"
        if metrics.get('days_variance') is not None and metrics['days_variance'] != 0:
            if metrics['days_variance'] > 0:
                summary += f" ({metrics['days_variance']} days late)"
            else:
                summary += f" ({abs(metrics['days_variance'])} days early)"
        summary += "\n"

    # Allocation comparison
    if allocation.get('estimated_allocation') and allocation.get('actual_allocation'):
        est = allocation['estimated_allocation']
        act = allocation['actual_allocation']
        variance = act - est

        summary += f"\n📊 **Capacity:**\n"
        summary += f"   • Estimated: {est}%\n"
        summary += f"   • Actual: {act}%\n"

        if abs(variance) <= 2:
            summary += f"   • Variance: On target! ✓\n"
        elif variance > 0:
            summary += f"   • Variance: +{variance:.1f}% (took more capacity than expected)\n"
        else:
            summary += f"   • Variance: {variance:.1f}% (completed under estimate)\n"

    return summary


def create_feedback_comment(task, summary):
    """Create the full feedback comment with summary and effort prompt"""

    comment = f"""📋 **Task Completion Summary**

{summary}

---

**📝 Effort Feedback Request**

To help improve our capacity estimates, please reply with your subjective assessment:

**How did the actual effort compare to what you expected?**
• 1️⃣ Much easier than expected
• 2️⃣ Somewhat easier than expected
• 3️⃣ About as expected
• 4️⃣ Somewhat harder than expected
• 5️⃣ Much harder than expected

**Any notes on what affected the effort?** (optional)
Examples: Client revisions, technical issues, scope changes, etc.

---
*This is an automated completion summary. Your feedback helps improve future estimates.*
"""

    return comment


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


def process_completed_task(task, posted_tasks):
    """Process a single completed task and post feedback"""
    task_gid = task['gid']
    task_name = task['name']

    # Skip if already processed
    if task_gid in posted_tasks:
        return False

    logger.info(f"Processing completed task: {task_name}")

    # Calculate metrics
    metrics = calculate_time_metrics(task)
    allocation = get_allocation_data(task)

    # Generate summary
    summary = generate_completion_summary_claude(task, metrics, allocation)

    # Create full feedback comment
    comment = create_feedback_comment(task, summary)

    # Post comment
    if add_comment_to_task(task_gid, comment):
        logger.info(f"✅ Posted feedback comment for: {task_name}")
        posted_tasks.add(task_gid)
        return True
    else:
        logger.error(f"❌ Failed to post feedback for: {task_name}")
        return False


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Post-Completion Feedback Collection - Starting")
    logger.info("=" * 60)

    # Check configuration
    if not ASANA_PAT:
        logger.error("ASANA_PAT_SCORER not found in environment")
        return

    # Load tracking data
    posted_tasks = load_feedback_tracking()
    logger.info(f"Loaded {len(posted_tasks)} previously processed tasks")

    # Fetch recently completed tasks
    completed_tasks = fetch_recently_completed_tasks()
    logger.info(f"Found {len(completed_tasks)} completed tasks in last 7 days")

    # Filter to tasks that haven't received feedback yet
    new_completions = [t for t in completed_tasks if t['gid'] not in posted_tasks]
    logger.info(f"Found {len(new_completions)} new completion(s) to process")

    if not new_completions:
        logger.info("No new completions to process")
    else:
        # Process each task
        success_count = 0
        for task in new_completions:
            if process_completed_task(task, posted_tasks):
                success_count += 1

        logger.info(f"\n✅ Posted feedback for {success_count}/{len(new_completions)} task(s)")

    # Save updated tracking
    save_feedback_tracking(posted_tasks)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Post-Completion Feedback Collection - Complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
