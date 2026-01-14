#!/usr/bin/env python3
"""
Weekly Capacity Report - Sends email every Monday at 8am
"""
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
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

# Team configuration
TEAM_CAPACITY = {
    "Zach Welliver": {"gid": "1205076276256605", "capacity": 50},
    "Nick Clark": {"gid": "1202206953008470", "capacity": 100},
    "Adriel Abella": {"gid": "1208249805795150", "capacity": 100},
    "John Meyer": {"gid": "1211292436943049", "capacity": 30}
}

PROJECTS = {
    "Preproduction": "1208336083003480",
    "Production": "1209597979075357",
    "Post Production": "1209581743268502"
}

PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"

def get_capacity_usage():
    """Get current capacity usage for all team members"""
    capacity_usage = {name: {"total": 0, "tasks": []} for name in TEAM_CAPACITY.keys()}

    for project_name, project_gid in PROJECTS.items():
        endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,custom_fields,completed,assignee"
        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]

            for task in tasks:
                if task.get('completed', False):
                    continue

                assignee = task.get('assignee')
                if not assignee:
                    continue

                assignee_gid = assignee.get('gid')

                for member_name, member_info in TEAM_CAPACITY.items():
                    if member_info["gid"] == assignee_gid:
                        allocation = 0
                        for cf in task.get('custom_fields', []):
                            if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                                allocation = ((cf.get('number_value', 0) or 0) * 100)  # Convert decimal to percentage
                                break

                        if allocation > 0:
                            capacity_usage[member_name]["total"] += allocation
                            capacity_usage[member_name]["tasks"].append({
                                "name": task["name"],
                                "allocation": allocation,
                                "project": project_name
                            })
                        break
        except Exception as e:
            print(f"Error fetching {project_name}: {e}")

    return capacity_usage

def generate_html_report(usage):
    """Generate HTML email report"""

    # Build summary table
    summary_rows = ""
    over_capacity_alerts = []

    for member_name, data in usage.items():
        total = data["total"]
        limit = TEAM_CAPACITY[member_name]["capacity"]
        percentage = (total / limit * 100) if limit > 0 else 0

        if total > limit:
            status = "🔴 OVER CAPACITY"
            status_color = "#dc3545"
            over_capacity_alerts.append(member_name)
        elif total > limit * 0.9:
            status = "🟡 Near Limit"
            status_color = "#ffc107"
        elif total > limit * 0.75:
            status = "🟠 High"
            status_color = "#fd7e14"
        else:
            status = "🟢 OK"
            status_color = "#28a745"

        summary_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #ddd;">{member_name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;"><strong>{total:.1f}%</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{limit}%</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{percentage:.0f}%</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: {status_color}; font-weight: bold;">{status}</td>
        </tr>
        """

    # Build detailed task breakdown
    task_breakdown = ""
    for member_name, data in usage.items():
        if data["tasks"]:
            task_list = ""
            sorted_tasks = sorted(data["tasks"], key=lambda x: x["allocation"], reverse=True)
            for task in sorted_tasks:  # All tasks
                task_list += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{task['allocation']:.1f}%</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{task['name']}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><em>{task['project']}</em></td>
                </tr>
                """

            task_breakdown += f"""
            <h3 style="color: #333; margin-top: 20px;">{member_name} - {data['total']:.1f}% ({len(sorted_tasks)} tasks)</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 80px;">Allocation</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Task</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd; width: 150px;">Project</th>
                    </tr>
                </thead>
                <tbody>
                    {task_list}
                </tbody>
            </table>
            """
        else:
            task_breakdown += f"""
            <h3 style="color: #333; margin-top: 20px;">{member_name}</h3>
            <p style="color: #666; font-style: italic;">No active tasks</p>
            """

    # Over-capacity alert section
    alert_section = ""
    if over_capacity_alerts:
        alert_items = "".join([f"<li style='margin: 8px 0;'><strong>{member}</strong> - {usage[member]['total']:.1f}% (limit: {TEAM_CAPACITY[member]['capacity']}%)</li>" for member in over_capacity_alerts])
        alert_section = f"""
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">⚠️ Capacity Alerts</h3>
            <ul style="color: #856404; margin: 10px 0;">
                {alert_items}
            </ul>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
            <h1 style="margin: 0;">📊 Weekly Team Capacity Report</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; margin-bottom: 20px;">
            {alert_section}

            <h2 style="color: #333; margin-top: 0;">Capacity Summary</h2>
            <table style="width: 100%; border-collapse: collapse; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #e9ecef;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Team Member</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Current Usage</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Limit</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Percentage</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {summary_rows}
                </tbody>
            </table>
        </div>

        <div style="background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-top: 0;">Task Breakdown</h2>
            {task_breakdown}
        </div>

        <div style="margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px; font-size: 12px; color: #666;">
            <p style="margin: 0;"><strong>Capacity Limits:</strong> Zach: 50% | Nick: 100% | Adriel: 100% | John: 30%</p>
            <p style="margin: 5px 0 0 0;"><em>Automated report from Video Production Capacity System</em></p>
        </div>
    </body>
    </html>
    """

    return html

def send_weekly_report():
    """Send weekly capacity report via email"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("❌ Email not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
        print(f"   SMTP_USER: {SMTP_USER or 'NOT SET'}")
        return False

    print(f"Generating weekly capacity report for {RECIPIENT_EMAIL}...")

    # Get capacity data
    usage = get_capacity_usage()

    # Generate HTML report
    html_content = generate_html_report(usage)

    # Create email
    subject = f"📊 Weekly Team Capacity Report - {datetime.now().strftime('%B %d, %Y')}"

    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_USER
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject

    # Attach HTML
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    # Send email
    try:
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        print(f"Logging in as {SMTP_USER}...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print(f"Sending email to {RECIPIENT_EMAIL}...")
        server.send_message(msg)
        server.quit()

        print(f"✅ Weekly report sent successfully to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == "__main__":
    send_weekly_report()
