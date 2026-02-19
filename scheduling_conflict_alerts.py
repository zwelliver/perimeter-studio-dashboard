#!/usr/bin/env python3
"""
Scheduling Conflict Alert System
Detects double-booked film dates (same date/time) and proximity warnings
(high-complexity shoots that may run into the next shoot on the same day).

Sends notifications via email, Slack, and file log.
Intended to run every 30 minutes via cron.
"""
import os
import sys
import json
import smtplib
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment from the script's own directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# --- Configuration (from config.py) ---
from config import (
    API, ALERTS, PATHS, FIELDS,
    VIDEO_PROJECT_GIDS, ASANA_HEADERS,
)

ASANA_PAT = API["ASANA_PAT_SCORER"]
ASANA_BASE_URL = API["ASANA_BASE_URL"]

ALERT_EMAIL_FROM = ALERTS["ALERT_EMAIL_FROM"]
ALERT_EMAIL_TO = ALERTS["ALERT_EMAIL_TO"]
SLACK_WEBHOOK = ALERTS.get("SLACK_WEBHOOK_CONFLICTS", "")
COMPLEXITY_THRESHOLD = ALERTS.get("CONFLICT_COMPLEXITY_THRESHOLD", 7)

CONFLICT_LOG_FILE = PATHS.get("CONFLICT_ALERTS_LOG",
    os.path.join(SCRIPT_DIR, "scheduling_conflict_alerts.txt"))
CONFLICT_STATE_FILE = PATHS.get("CONFLICT_ALERT_STATE",
    os.path.join(SCRIPT_DIR, "scheduling_conflict_state.json"))

FILM_DATE_FIELD_GID = FIELDS["Film Date"]["gid"]
COMPLEXITY_FIELD_GID = FIELDS["Complexity"]["gid"]
VIDEOGRAPHER_FIELD_GID = FIELDS["Videographer"]["gid"]


# =============================================================================
# Asana Data Fetching
# =============================================================================

def fetch_upcoming_shoots():
    """Fetch all incomplete tasks with Film Date set from production projects."""
    if not ASANA_PAT:
        print("ASANA_PAT_SCORER not set — cannot fetch tasks.")
        return [], {}

    shoots = []
    complexity_by_gid = {}
    now = datetime.now(timezone.utc)

    for project_name, project_gid in VIDEO_PROJECT_GIDS.items():
        endpoint = f"{ASANA_BASE_URL}/projects/{project_gid}/tasks"
        params = {
            'opt_fields': 'gid,name,completed,custom_fields,assignee.name'
        }

        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS, params=params)
            response.raise_for_status()
            tasks = response.json().get('data', [])
        except Exception as e:
            print(f"Warning: Could not fetch tasks from {project_name}: {e}")
            continue

        for task in tasks:
            if task.get('completed', False):
                continue

            film_datetime = None
            complexity = 0
            videographer = None

            for field in task.get('custom_fields', []):
                fgid = field.get('gid')
                if fgid == FILM_DATE_FIELD_GID:
                    date_value = field.get('date_value')
                    if date_value:
                        film_str = date_value.get('date_time') or date_value.get('date')
                        if film_str:
                            if 'T' in film_str or 'Z' in film_str:
                                film_datetime = datetime.fromisoformat(
                                    film_str.replace('Z', '+00:00'))
                            else:
                                from datetime import date as date_type
                                d = date_type.fromisoformat(film_str)
                                film_datetime = datetime.combine(
                                    d, datetime.min.time()).replace(tzinfo=timezone.utc)
                elif fgid == COMPLEXITY_FIELD_GID:
                    complexity = field.get('number_value', 0) or 0
                elif fgid == VIDEOGRAPHER_FIELD_GID:
                    videographer = field.get('display_value') or field.get('text_value')

            if film_datetime and film_datetime >= now:
                assignee_name = 'Unassigned'
                if task.get('assignee'):
                    assignee_name = task['assignee'].get('name', 'Unassigned')

                task_name = task.get('name', 'Untitled')
                task_name = task_name.replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()

                shoots.append({
                    'name': task_name,
                    'datetime': film_datetime,
                    'project': project_name,
                    'gid': task.get('gid'),
                    'assignee': assignee_name,
                    'videographer': videographer or '',
                })
                complexity_by_gid[task.get('gid')] = complexity

    shoots.sort(key=lambda x: x['datetime'])
    return shoots, complexity_by_gid


# =============================================================================
# Conflict Detection (mirrors generate_dashboard.py logic)
# =============================================================================

def detect_conflicts(shoots, complexity_by_gid):
    """Detect scheduling conflicts.

    Returns:
        list of conflict dicts with keys: date, type ('hard'/'soft'), label, tasks
    """
    if not shoots:
        return []

    by_date = defaultdict(list)
    for shoot in shoots:
        date_key = shoot['datetime'].strftime('%Y-%m-%d')
        by_date[date_key].append(shoot)

    conflicts = []

    for date_key, day_shoots in by_date.items():
        if len(day_shoots) < 2:
            continue

        day_shoots_sorted = sorted(day_shoots, key=lambda s: s['datetime'])

        # Hard conflicts: exact same datetime
        by_time = defaultdict(list)
        for shoot in day_shoots_sorted:
            time_key = shoot['datetime'].strftime('%Y-%m-%d %H:%M')
            by_time[time_key].append(shoot)

        hard_conflict_gids = set()
        for time_key, time_group in by_time.items():
            if len(time_group) >= 2:
                conflicts.append({
                    'date': date_key,
                    'type': 'hard',
                    'label': 'Same date/time',
                    'tasks': _task_summaries(time_group),
                })
                for s in time_group:
                    hard_conflict_gids.add(s.get('gid'))

        # Soft conflicts: high-complexity earlier shoot may run into next
        if len(day_shoots_sorted) >= 2:
            for i in range(len(day_shoots_sorted) - 1):
                earlier = day_shoots_sorted[i]
                later = day_shoots_sorted[i + 1]

                if earlier.get('gid') in hard_conflict_gids and later.get('gid') in hard_conflict_gids:
                    continue

                earlier_complexity = complexity_by_gid.get(earlier.get('gid'), 0) or 0
                if earlier_complexity >= COMPLEXITY_THRESHOLD:
                    conflicts.append({
                        'date': date_key,
                        'type': 'soft',
                        'label': f'High-complexity shoot (score: {earlier_complexity}) may run into next',
                        'tasks': _task_summaries([earlier, later]),
                    })

    conflicts.sort(key=lambda c: (c['date'], 0 if c['type'] == 'hard' else 1))
    return conflicts


def _task_summaries(task_list):
    return [
        {
            'name': t.get('name', 'Untitled'),
            'project': t.get('project', ''),
            'assignee': t.get('assignee', 'Unassigned'),
            'videographer': t.get('videographer', ''),
            'gid': t.get('gid', ''),
            'datetime': t['datetime'].isoformat(),
        }
        for t in task_list
    ]


# =============================================================================
# State Tracking (avoid re-alerting on the same conflict)
# =============================================================================

def _conflict_key(conflict):
    """Generate a unique key for a conflict based on date + involved task GIDs."""
    gids = sorted(t.get('gid', '') for t in conflict['tasks'])
    return f"{conflict['date']}|{conflict['type']}|{'_'.join(gids)}"


def load_alerted_state():
    if os.path.exists(CONFLICT_STATE_FILE):
        try:
            with open(CONFLICT_STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_alerted_state(state):
    with open(CONFLICT_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def filter_new_conflicts(conflicts, state):
    """Return only conflicts not already alerted."""
    new = []
    for c in conflicts:
        key = _conflict_key(c)
        if key not in state:
            new.append(c)
    return new


def mark_alerted(conflicts, state):
    """Mark conflicts as alerted in state."""
    for c in conflicts:
        key = _conflict_key(c)
        state[key] = datetime.now(timezone.utc).isoformat()
    return state


def prune_old_state(state):
    """Remove state entries for dates that have passed."""
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    pruned = {}
    for key, ts in state.items():
        date_part = key.split('|')[0]
        if date_part >= today_str:
            pruned[key] = ts
    return pruned


# =============================================================================
# Notification Channels
# =============================================================================

def _format_conflict_text(conflict):
    """Plain-text summary of a single conflict."""
    type_label = "TIME CONFLICT" if conflict['type'] == 'hard' else "PROXIMITY WARNING"
    lines = [
        f"[{type_label}] {conflict['date']} — {conflict['label']}",
    ]
    for t in conflict['tasks']:
        dt_str = t.get('datetime', '')
        if 'T' in dt_str:
            try:
                dt = datetime.fromisoformat(dt_str)
                time_str = dt.astimezone().strftime('%-I:%M %p')
            except Exception:
                time_str = dt_str
        else:
            time_str = 'TBD'
        vid = f" | Videographer: {t['videographer']}" if t.get('videographer') else ""
        lines.append(f"  • {t['name']} — {time_str} | {t['project']} | {t['assignee']}{vid}")
    return "\n".join(lines)


def send_email_alert(conflicts):
    """Send HTML email listing all new scheduling conflicts."""
    smtp_user = API.get("SMTP_USERNAME")
    smtp_pass = API.get("SMTP_PASSWORD")
    if not smtp_user or not smtp_pass:
        print("Email not configured (SMTP_USERNAME / SMTP_PASSWORD)")
        return False

    hard = [c for c in conflicts if c['type'] == 'hard']
    soft = [c for c in conflicts if c['type'] == 'soft']

    subject = f"⚠️ Scheduling Conflict{'s' if len(conflicts) != 1 else ''}: {len(hard)} time conflict{'s' if len(hard) != 1 else ''}"
    if soft:
        subject += f", {len(soft)} proximity warning{'s' if len(soft) != 1 else ''}"

    rows = ""
    for c in conflicts:
        color = "#dc3545" if c['type'] == 'hard' else "#e6a000"
        badge = "TIME CONFLICT" if c['type'] == 'hard' else "PROXIMITY WARNING"
        task_lines = ""
        for t in c['tasks']:
            dt_str = t.get('datetime', '')
            try:
                dt = datetime.fromisoformat(dt_str)
                time_str = dt.astimezone().strftime('%-I:%M %p')
            except Exception:
                time_str = 'TBD'
            vid = f" | Videographer: {t['videographer']}" if t.get('videographer') else ""
            task_lines += f"<li>{t['name']} — {time_str} | {t['project']} | {t['assignee']}{vid}</li>"

        rows += f"""
        <div style="border-left: 4px solid {color}; padding: 10px 14px; margin-bottom: 14px; background: #f9f9f9;">
            <strong>{c['date']}</strong>
            <span style="background: {color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 8px;">{badge}</span>
            <div style="font-size: 13px; color: #666; margin: 4px 0;">{c['label']}</div>
            <ul style="margin: 6px 0; padding-left: 20px;">{task_lines}</ul>
        </div>
        """

    body = f"""
    <html><body style="font-family: -apple-system, sans-serif; color: #333;">
    <h2 style="color: #09243F;">Scheduling Conflict Alert</h2>
    {rows}
    <hr style="border: none; border-top: 1px solid #ddd; margin-top: 20px;">
    <p style="font-size: 12px; color: #999;">Automated alert from Studio Scheduling Conflict System</p>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = ALERT_EMAIL_FROM
        msg['To'] = ALERT_EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(API["SMTP_SERVER"], API["SMTP_PORT"])
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email alert sent to {ALERT_EMAIL_TO}")
        return True
    except Exception as e:
        print(f"❌ Email alert failed: {e}")
        return False


def send_slack_alert(conflicts):
    """Send Slack block-formatted message for each new conflict."""
    if not SLACK_WEBHOOK:
        print("Slack not configured (SLACK_WEBHOOK_CONFLICTS)")
        return False

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"⚠️ {len(conflicts)} Scheduling Conflict{'s' if len(conflicts) != 1 else ''} Detected"
            }
        }
    ]

    for c in conflicts:
        badge = "🔴 TIME CONFLICT" if c['type'] == 'hard' else "🟡 PROXIMITY WARNING"
        task_lines = []
        for t in c['tasks']:
            dt_str = t.get('datetime', '')
            try:
                dt = datetime.fromisoformat(dt_str)
                time_str = dt.astimezone().strftime('%-I:%M %p')
            except Exception:
                time_str = 'TBD'
            vid = f" | Videographer: {t['videographer']}" if t.get('videographer') else ""
            task_lines.append(f"• {t['name']} — {time_str} | {t['project']} | {t['assignee']}{vid}")

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{c['date']}* — {badge}\n_{c['label']}_\n" + "\n".join(task_lines)
            }
        })

    message = {
        "text": f"⚠️ {len(conflicts)} scheduling conflict(s) detected",
        "blocks": blocks,
    }

    try:
        response = requests.post(SLACK_WEBHOOK, json=message)
        response.raise_for_status()
        print("✅ Slack alert sent")
        return True
    except Exception as e:
        print(f"❌ Slack alert failed: {e}")
        return False


def log_to_file(conflicts):
    """Append conflicts to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entries = []
    entries.append(f"\n{'='*70}")
    entries.append(f"SCHEDULING CONFLICT ALERT — {timestamp}")
    entries.append(f"{'='*70}")
    for c in conflicts:
        entries.append(_format_conflict_text(c))
    entries.append(f"{'='*70}\n")

    with open(CONFLICT_LOG_FILE, 'a') as f:
        f.write("\n".join(entries) + "\n")

    print(f"✅ Alert logged to {CONFLICT_LOG_FILE}")


# =============================================================================
# Main
# =============================================================================

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for scheduling conflicts...")

    shoots, complexity_by_gid = fetch_upcoming_shoots()
    print(f"  Found {len(shoots)} upcoming shoots across {len(VIDEO_PROJECT_GIDS)} projects")

    conflicts = detect_conflicts(shoots, complexity_by_gid)
    print(f"  Detected {len(conflicts)} conflict(s)")

    if not conflicts:
        print("  No conflicts found. Done.")
        return

    # Filter out already-alerted conflicts
    state = load_alerted_state()
    state = prune_old_state(state)
    new_conflicts = filter_new_conflicts(conflicts, state)

    if not new_conflicts:
        print("  All conflicts already alerted. Done.")
        save_alerted_state(state)
        return

    hard = [c for c in new_conflicts if c['type'] == 'hard']
    soft = [c for c in new_conflicts if c['type'] == 'soft']
    print(f"  New: {len(hard)} time conflict(s), {len(soft)} proximity warning(s)")

    # Send notifications
    log_to_file(new_conflicts)
    send_email_alert(new_conflicts)
    send_slack_alert(new_conflicts)

    # Update state
    state = mark_alerted(new_conflicts, state)
    save_alerted_state(state)

    print("  Done.")


if __name__ == "__main__":
    main()
