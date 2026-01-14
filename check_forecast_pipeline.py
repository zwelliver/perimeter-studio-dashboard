#!/usr/bin/env python3
"""
Forecast to Pipeline Checker
Sends email alerts for forecasted projects that haven't been moved to production pipeline
when they are within 30 days of their due date.
"""

import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv(".env")

ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "studio@perimeter.org")
EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "zach@perimeter.org")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Asana project GIDs
FORECAST_PROJECT_GID = '1212059678473189'
PRODUCTION_PROJECT_GIDS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502'
}

def fetch_forecasted_projects():
    """Fetch all incomplete tasks from Forecast project"""
    if not ASANA_PAT:
        print("Error: ASANA_PAT_SCORER not found in environment")
        return []

    headers = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

    endpoint = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}/tasks"
    params = {
        'opt_fields': 'gid,name,start_on,due_on,due_at,completed'
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        tasks = response.json().get('data', [])
        forecasted = []

        for task in tasks:
            if task.get('completed', False):
                continue

            # Extract due date
            due_date = None
            if task.get('due_on'):
                due_date = datetime.strptime(task['due_on'], '%Y-%m-%d').date()
            elif task.get('due_at'):
                due_datetime = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
                due_date = due_datetime.date()

            # Parse start_on if available
            start_date = None
            if task.get('start_on'):
                start_date = datetime.strptime(task['start_on'], '%Y-%m-%d').date()

            forecasted.append({
                'gid': task.get('gid'),
                'name': task.get('name', 'Untitled'),
                'start_on': start_date,
                'due_date': due_date
            })

        return forecasted

    except Exception as e:
        print(f"Error fetching forecasted projects: {e}")
        return []

def fetch_pipeline_project_names():
    """Fetch all task names from production pipeline projects"""
    if not ASANA_PAT:
        return set()

    headers = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

    pipeline_names = set()

    for project_name, project_gid in PRODUCTION_PROJECT_GIDS.items():
        try:
            endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
            params = {'opt_fields': 'name,completed'}

            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()

            tasks = response.json().get('data', [])

            # Add all task names (both completed and incomplete) to check against
            for task in tasks:
                name = task.get('name', '').strip()
                if name:
                    # Normalize name - remove checkboxes and extra whitespace
                    clean_name = name.replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()
                    pipeline_names.add(clean_name.lower())

            print(f"Found {len(tasks)} tasks in {project_name}")

        except Exception as e:
            print(f"Error fetching {project_name} tasks: {e}")

    return pipeline_names

def check_forecast_alerts():
    """Check for forecasted projects that need to be moved to pipeline"""

    print("Checking forecasted projects...")

    # Fetch data
    forecasted_projects = fetch_forecasted_projects()
    pipeline_names = fetch_pipeline_project_names()

    print(f"Found {len(forecasted_projects)} forecasted projects")
    print(f"Found {len(pipeline_names)} projects in pipeline")

    # Find projects that are within 30 days and not in pipeline
    alerts = []
    now = datetime.now().date()
    threshold_date = now + timedelta(days=30)

    for project in forecasted_projects:
        # Skip projects without due dates
        if not project['due_date']:
            continue

        # Check if within 30 days
        if project['due_date'] <= threshold_date:
            # Check if NOT in pipeline
            clean_name = project['name'].replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()

            if clean_name.lower() not in pipeline_names:
                days_until = (project['due_date'] - now).days

                alerts.append({
                    'name': project['name'],
                    'due_date': project['due_date'],
                    'days_until': days_until,
                    'gid': project['gid']
                })

    return alerts

def send_email_alert(alerts):
    """Send email notification for projects that need attention"""

    if not alerts:
        print("No alerts to send")
        return

    if not all([SMTP_USERNAME, SMTP_PASSWORD, EMAIL_TO]):
        print("Error: Email configuration incomplete")
        print("Required: SMTP_USERNAME, SMTP_PASSWORD, ALERT_EMAIL_TO in .env")
        return

    # Build email content
    subject = f"⚠️ Forecast Alert: {len(alerts)} project{'s' if len(alerts) > 1 else ''} need{'s' if len(alerts) == 1 else ''} to move to pipeline"

    # Sort by days until due
    alerts.sort(key=lambda x: x['days_until'])

    # HTML email body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #09243F;
                border-bottom: 3px solid #60BBE9;
                padding-bottom: 10px;
            }}
            .alert-box {{
                background: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .project-card {{
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
            }}
            .project-name {{
                font-size: 18px;
                font-weight: 600;
                color: #09243F;
                margin-bottom: 8px;
            }}
            .project-due {{
                color: #6c757d;
                margin-bottom: 5px;
            }}
            .urgent {{
                color: #dc3545;
                font-weight: bold;
            }}
            .warning {{
                color: #ffc107;
                font-weight: bold;
            }}
            .link {{
                display: inline-block;
                margin-top: 10px;
                color: #60BBE9;
                text-decoration: none;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                font-size: 12px;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Forecast Pipeline Alert</h1>

            <div class="alert-box">
                <strong>Action Required:</strong> The following forecasted projects are within 30 days of their due date
                but have not been moved to the production pipeline yet.
            </div>

            <p>Found <strong>{len(alerts)}</strong> project{'s' if len(alerts) > 1 else ''} that need{'s' if len(alerts) == 1 else ''} attention:</p>
    """

    for alert in alerts:
        # Determine urgency
        if alert['days_until'] <= 7:
            urgency_class = "urgent"
            urgency_text = f"⚠️ DUE IN {alert['days_until']} DAYS"
        elif alert['days_until'] <= 14:
            urgency_class = "warning"
            urgency_text = f"Due in {alert['days_until']} days"
        else:
            urgency_class = ""
            urgency_text = f"Due in {alert['days_until']} days"

        task_url = f"https://app.asana.com/0/0/{alert['gid']}/f"
        due_str = alert['due_date'].strftime('%A, %B %-d, %Y')

        html_body += f"""
            <div class="project-card">
                <div class="project-name">{alert['name']}</div>
                <div class="project-due">Due: {due_str}</div>
                <div class="{urgency_class}">{urgency_text}</div>
                <a href="{task_url}" class="link" target="_blank">View in Asana →</a>
            </div>
        """

    html_body += """
            <div class="footer">
                <p>This is an automated alert from the Perimeter Studio Capacity Dashboard.</p>
                <p>To stop receiving these alerts, update your .env configuration or disable the automation.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    # Plain text version
    text_body = f"""
Forecast Pipeline Alert

{len(alerts)} project{'s' if len(alerts) > 1 else ''} need{'s' if len(alerts) == 1 else ''} to be moved to production pipeline:

"""

    for alert in alerts:
        text_body += f"""
Project: {alert['name']}
Due: {alert['due_date'].strftime('%A, %B %-d, %Y')}
Days Until Due: {alert['days_until']}
Link: https://app.asana.com/0/0/{alert['gid']}/f

"""

    text_body += """
---
This is an automated alert from the Perimeter Studio Capacity Dashboard.
"""

    # Attach both versions
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {EMAIL_TO}")
        print(f"   Subject: {subject}")

    except Exception as e:
        print(f"❌ Error sending email: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("Perimeter Studio - Forecast Pipeline Checker")
    print("=" * 60)
    print()

    alerts = check_forecast_alerts()

    if alerts:
        print()
        print(f"⚠️  Found {len(alerts)} project(s) requiring attention:")
        for alert in sorted(alerts, key=lambda x: x['days_until']):
            print(f"   - {alert['name']} (due in {alert['days_until']} days)")

        print()
        send_email_alert(alerts)
    else:
        print("✅ All forecasted projects are either in the pipeline or not due soon")

    print()
    print("=" * 60)

if __name__ == '__main__':
    main()
