#!/usr/bin/env python3
"""
WOV Completion Alert - Sends email on Wednesdays at 4pm
if WOV projects due that week aren't complete yet
"""
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(".env")

# Configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT}"}

RECIPIENT_EMAIL = "zwelliver@perimeter.org"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Production project where WOV tasks live
PRODUCTION_PROJECT_GID = "1209597979075357"

def get_week_bounds():
    """Get the start (Sunday) and end (Saturday) of the current week"""
    today = datetime.now().date()
    # Get the most recent Sunday (start of week)
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end

def get_incomplete_wov_tasks():
    """Get WOV tasks due this week that aren't completed yet"""
    week_start, week_end = get_week_bounds()

    incomplete_wov_tasks = []

    # Fetch all tasks from Production project
    endpoint = f"https://app.asana.com/api/1.0/projects/{PRODUCTION_PROJECT_GID}/tasks"
    params = {
        'opt_fields': 'gid,name,completed,due_on,due_at,permalink_url,assignee.name'
    }

    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()["data"]

        for task in tasks:
            # Skip if already completed
            if task.get('completed', False):
                continue

            # Check if this is a WOV task (has "WOV" in the name)
            task_name = task.get('name', '')
            if 'WOV' not in task_name.upper():
                continue

            # Check if task has a due date
            due_date = None
            if task.get('due_at'):
                # Parse datetime string
                due_datetime = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
                due_date = due_datetime.date()
            elif task.get('due_on'):
                # Parse date string
                due_date = datetime.strptime(task['due_on'], '%Y-%m-%d').date()

            # Skip if no due date
            if not due_date:
                continue

            # Check if due date falls within this week (Sunday - Saturday)
            if week_start <= due_date <= week_end:
                assignee_name = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'

                incomplete_wov_tasks.append({
                    'name': task_name,
                    'due_date': due_date,
                    'assignee': assignee_name,
                    'url': task.get('permalink_url', '')
                })

    except Exception as e:
        print(f"Error fetching WOV tasks: {e}")
        return None

    return incomplete_wov_tasks

def generate_html_alert(tasks):
    """Generate HTML email alert"""
    week_start, week_end = get_week_bounds()

    task_rows = ""
    for task in tasks:
        task_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                    <a href="{task['url']}" style="color: #60BBE9; text-decoration: none; font-weight: 500;">
                        {task['name']}
                    </a>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                    {task['due_date'].strftime('%A, %b %d')}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                    {task['assignee']}
                </td>
            </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">⚠️ WOV Completion Alert</h1>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">
                    Wednesday, {datetime.now().strftime('%B %d, %Y')} at 4:00 PM
                </p>
            </div>

            <!-- Alert Message -->
            <div style="padding: 30px;">
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 25px; border-radius: 4px;">
                    <p style="margin: 0; font-size: 15px; color: #856404;">
                        <strong>{len(tasks)} WOV task{"s" if len(tasks) != 1 else ""}</strong> due this week (ending {week_end.strftime('%B %d')}) {"are" if len(tasks) != 1 else "is"} not yet marked complete.
                    </p>
                </div>

                <h2 style="color: #09243F; font-size: 18px; margin-bottom: 15px; border-bottom: 2px solid #60BBE9; padding-bottom: 10px;">
                    Incomplete WOV Tasks
                </h2>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #60BBE9; color: #09243F; font-weight: 600;">
                                Task
                            </th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #60BBE9; color: #09243F; font-weight: 600;">
                                Due Date
                            </th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #60BBE9; color: #09243F; font-weight: 600;">
                                Assigned To
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {task_rows}
                    </tbody>
                </table>

                <div style="background: #e8f4f8; border-left: 4px solid #60BBE9; padding: 15px; border-radius: 4px; margin-top: 20px;">
                    <p style="margin: 0; font-size: 14px; color: #09243F;">
                        <strong>💡 Reminder:</strong> WOV tasks should be completed by Wednesday afternoon to ensure they're ready for Sunday publication.
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                <p style="margin: 0; font-size: 12px; color: #6c757d;">
                    This is an automated alert from the Studio Automation System
                </p>
                <p style="margin: 5px 0 0 0; font-size: 11px; color: #adb5bd;">
                    Sent every Wednesday at 4:00 PM
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html

def send_email(subject, html_content):
    """Send email alert"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️  Email credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = RECIPIENT_EMAIL

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Alert email sent to {RECIPIENT_EMAIL}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Checking for incomplete WOV tasks...")

    # Get incomplete WOV tasks due this week
    tasks = get_incomplete_wov_tasks()

    if tasks is None:
        print("❌ Error fetching tasks from Asana")
        return

    if not tasks:
        print("✅ All WOV tasks due this week are complete!")
        return

    print(f"⚠️  Found {len(tasks)} incomplete WOV task(s) due this week:")
    for task in tasks:
        print(f"  - {task['name']} (Due: {task['due_date'].strftime('%A, %b %d')})")

    # Generate and send alert email
    week_start, week_end = get_week_bounds()
    subject = f"⚠️ WOV Completion Alert - {len(tasks)} Task{'s' if len(tasks) != 1 else ''} Incomplete"
    html_content = generate_html_alert(tasks)

    send_email(subject, html_content)

if __name__ == "__main__":
    main()
