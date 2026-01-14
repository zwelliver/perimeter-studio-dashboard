#!/usr/bin/env python3
"""
Capacity Alert System
Sends notifications when team members are over capacity
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(".env")

# Alert configuration
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "zwelliver@perimeter.org")  # Zach Welliver
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App-specific password

# Slack webhook (optional)
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_CAPACITY", "")

def send_email_alert(member_name, current_usage, limit, tasks):
    """Send email alert for over-capacity situation"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Email not configured (set SMTP_USER and SMTP_PASSWORD in .env)")
        return False

    subject = f"⚠️ Capacity Alert: {member_name} Over Capacity"

    task_list = "\n".join([f"  • {t['allocation']:.1f}% - {t['name']}" for t in tasks])

    body = f"""
Team Capacity Alert
===================

{member_name} is currently OVER CAPACITY:

Current Usage: {current_usage:.1f}%
Capacity Limit: {limit}%
Over by: {current_usage - limit:.1f}%

All Assigned Tasks ({len(tasks)} total):
{task_list}

Please review and adjust assignments.

---
Automated alert from Video Production Capacity System
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email alert sent to {ALERT_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ Email alert failed: {e}")
        return False

def send_slack_alert(member_name, current_usage, limit, tasks):
    """Send Slack notification for over-capacity situation"""
    if not SLACK_WEBHOOK:
        print("Slack not configured (set SLACK_WEBHOOK_CAPACITY in .env)")
        return False

    task_list = "\n".join([f"  • {t['allocation']:.1f}% - {t['name']}" for t in tasks])

    message = {
        "text": f"⚠️ *Capacity Alert: {member_name} Over Capacity*",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ {member_name} Over Capacity"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Usage:*\n{current_usage:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Limit:*\n{limit}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Over by:*\n{current_usage - limit:.1f}%"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*All Assigned Tasks ({len(tasks)} total):*\n{task_list}"
                }
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK, json=message)
        response.raise_for_status()
        print("✅ Slack alert sent")
        return True
    except Exception as e:
        print(f"❌ Slack alert failed: {e}")
        return False

def send_asana_comment_alert(member_gid, member_name, current_usage, limit):
    """Create an Asana task for manual review"""
    ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
    if not ASANA_PAT:
        print("Asana not configured")
        return False

    # You could create a task in a specific project for alerts
    # For now, just log it
    print(f"📝 Asana alert: {member_name} over capacity ({current_usage:.1f}% / {limit}%)")
    return True

def log_alert_to_file(member_name, current_usage, limit, tasks):
    """Write alert to a simple text file"""
    alert_file = os.path.expanduser("~/Scripts/StudioProcesses/capacity_alerts.txt")

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    task_list = "\n".join([f"    • {t['allocation']:.1f}% - {t['name']}" for t in tasks])

    alert_text = f"""
{'='*70}
CAPACITY ALERT - {timestamp}
{'='*70}
Team Member: {member_name}
Current Usage: {current_usage:.1f}%
Limit: {limit}%
Over by: {current_usage - limit:.1f}%

All Assigned Tasks ({len(tasks)} total):
{task_list}
{'='*70}

"""

    with open(alert_file, 'a') as f:
        f.write(alert_text)

    print(f"✅ Alert logged to {alert_file}")
    return True

if __name__ == "__main__":
    # Test alert system
    print("Testing alert system...")

    test_tasks = [
        {"name": "Test Project 1", "allocation": 15.5},
        {"name": "Test Project 2", "allocation": 12.0}
    ]

    # File alert always works
    log_alert_to_file("Test User", 110.0, 100.0, test_tasks)

    # Try other methods
    # send_email_alert("Test User", 110.0, 100.0, test_tasks)
    # send_slack_alert("Test User", 110.0, 100.0, test_tasks)
