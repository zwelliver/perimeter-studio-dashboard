"""
Perimeter Studio Capacity Dashboard Generator
Generates interactive HTML dashboard
"""

import pandas as pd
import os
import json
import math
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader

# Perimeter Church Brand Colors
BRAND_NAVY = '#09243F'
BRAND_BLUE = '#60BBE9'
BRAND_OFF_WHITE = '#f8f9fa'

def read_reports():
    """Read all report CSV files and fetch active task data from Asana"""
    import requests
    import os
    from dotenv import load_dotenv

    load_dotenv(".env")

    reports_dir = 'Reports'

    data = {
        'allocation': None,
        'variance': None,
        'delivery_log': None,
        'delivery_summary': None,
        'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'team_capacity': [],
        'capacity_history': None
    }

    # Read allocation report
    allocation_file = os.path.join(reports_dir, 'weighted_allocation_report.csv')
    if os.path.exists(allocation_file):
        data['allocation'] = pd.read_csv(allocation_file)

    # Read variance tracking
    variance_file = os.path.join(reports_dir, 'variance_tracking_history.csv')
    if os.path.exists(variance_file):
        df = pd.read_csv(variance_file)
        if not df.empty:
            # Calculate cumulative averages across all time
            cumulative_variance = df.groupby('Category').agg({
                'Actual %': 'mean',
                'Target %': 'first',  # Target is constant
                'Variance': 'mean'
            }).reset_index()

            data['variance'] = cumulative_variance
            # Keep full history for trends
            data['variance_history'] = df

    # Read delivery performance log
    delivery_log_file = os.path.join(reports_dir, 'delivery_performance_log.csv')
    if os.path.exists(delivery_log_file):
        data['delivery_log'] = pd.read_csv(delivery_log_file)

    # Read delivery performance summary
    delivery_summary_file = os.path.join(reports_dir, 'delivery_performance_summary.csv')
    if os.path.exists(delivery_summary_file):
        # This is a text file, parse it
        with open(delivery_summary_file, 'r') as f:
            content = f.read()
            data['delivery_summary'] = content

    # Read capacity history
    capacity_history_file = os.path.join(reports_dir, 'capacity_history.csv')
    if os.path.exists(capacity_history_file):
        capacity_df = pd.read_csv(capacity_history_file)
        # Sort by date to ensure chronological order
        capacity_df = capacity_df.sort_values('date')

        # Filter to show only last 30 days for cleaner chart display
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        capacity_df = capacity_df[capacity_df['date'] >= cutoff_date]

        # Organize data by team member
        capacity_history_by_member = {}
        team_members = ['Zach Welliver', 'Nick Clark', 'Adriel Abella', 'John Meyer', 'Team Total']

        for member in team_members:
            member_data = capacity_df[capacity_df['team_member'] == member]
            if not member_data.empty:
                capacity_history_by_member[member] = member_data[['date', 'utilization_percent']].to_dict('records')

        data['capacity_history_by_member'] = capacity_history_by_member
    else:
        data['capacity_history_by_member'] = {}

    # Fetch active tasks from Asana to calculate team capacity accurately
    team_capacity_config = {
        'Zach Welliver': {'max': 100},
        'Nick Clark': {'max': 100},
        'Adriel Abella': {'max': 100},
        'John Meyer': {'max': 30}
    }

    # Calculate current usage per team member from actual Asana tasks
    team_usage = {name: 0 for name in team_capacity_config.keys()}

    # Asana API setup
    ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
    if ASANA_PAT:
        headers = {
            "Authorization": f"Bearer {ASANA_PAT}",
            "Content-Type": "application/json"
        }

        # Internal projects (affect team capacity)
        project_gids = {
            'Preproduction': '1208336083003480',
            'Production': '1209597979075357',
            'Post Production': '1209581743268502',
            'Forecast': '1212059678473189'
        }

        # External projects (tracking only, do not affect team capacity)
        external_project_gids = {
            'Contracted/Outsourced': '1212319598244265'
        }

        PERCENT_ALLOCATION_FIELD_GID = '1208923995383367'

        # Fetch active tasks from all production projects
        for project_name, project_gid in project_gids.items():
            try:
                endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
                params = {
                    'opt_fields': 'gid,name,assignee.name,custom_fields,completed'
                }

                response = requests.get(endpoint, headers=headers, params=params)

                if response.status_code == 200:
                    tasks = response.json().get('data', [])

                    for task in tasks:
                        # Skip completed tasks
                        if task.get('completed', False):
                            continue

                        # Get assignee name
                        assignee = task.get('assignee')
                        if not assignee:
                            continue

                        assignee_name = assignee.get('name', '')

                        # Find Percent Allocation custom field
                        allocation_pct = 0
                        for field in task.get('custom_fields', []):
                            if field.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                                # Asana stores as decimal (0.13 = 13%), convert to percentage
                                allocation_pct = (field.get('number_value', 0) or 0) * 100
                                break

                        # Add to team member's usage if they're in our config
                        if assignee_name in team_usage:
                            team_usage[assignee_name] += allocation_pct

            except Exception as e:
                # If API call fails, continue with next project
                print(f"Warning: Could not fetch tasks from {project_name}: {e}")
                continue

    # Create team capacity list
    data['team_capacity'] = [
        {'name': name, 'current': team_usage[name], 'max': config['max']}
        for name, config in team_capacity_config.items()
    ]

    # Count actual active tasks from Asana
    data['active_task_count'] = 0
    if ASANA_PAT:
        for project_name, project_gid in project_gids.items():
            try:
                endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
                params = {'opt_fields': 'completed'}

                response = requests.get(endpoint, headers=headers, params=params)

                if response.status_code == 200:
                    tasks = response.json().get('data', [])
                    data['active_task_count'] += sum(1 for task in tasks if not task.get('completed', False))
            except Exception as e:
                print(f"Warning: Could not count tasks from {project_name}: {e}")
                continue

    # Fetch external project tasks (contracted/outsourced)
    data['external_projects'] = []
    if ASANA_PAT:
        VIDEOGRAPHER_FIELD_GID = '1209693890455555'
        for project_name, project_gid in external_project_gids.items():
            try:
                endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
                params = {'opt_fields': 'name,completed,due_on,custom_fields'}

                response = requests.get(endpoint, headers=headers, params=params)

                if response.status_code == 200:
                    tasks = response.json().get('data', [])
                    active_tasks = [t for t in tasks if not t.get('completed', False)]
                    completed_tasks = [t for t in tasks if t.get('completed', False)]

                    # Extract task info including videographer
                    task_list = []
                    for t in active_tasks[:5]:  # Show first 5
                        videographer = None
                        # Extract videographer from custom fields
                        for field in t.get('custom_fields', []):
                            if field.get('gid') == VIDEOGRAPHER_FIELD_GID:
                                videographer = field.get('text_value')
                                break

                        task_list.append({
                            'name': t.get('name', 'Untitled'),
                            'due_on': t.get('due_on'),
                            'videographer': videographer
                        })

                    data['external_projects'].append({
                        'name': project_name,
                        'active_count': len(active_tasks),
                        'completed_count': len(completed_tasks),
                        'total_count': len(tasks),
                        'tasks': task_list
                    })
            except Exception as e:
                print(f"Warning: Could not fetch external project {project_name}: {e}")
                continue

    # Fetch detailed task data for advanced analytics
    detailed_tasks = fetch_detailed_tasks()

    # Calculate workload forecast (7/14/30 days)
    data['workload_forecast'] = calculate_workload_forecast(detailed_tasks, team_capacity_config)

    # Identify at-risk tasks
    team_capacity_info = {}
    for member in data['team_capacity']:
        team_capacity_info[member['name']] = {
            'current': member['current'],
            'max': member['max']
        }
    data['at_risk_tasks'] = identify_at_risk_tasks(detailed_tasks, team_capacity_info)

    # Generate capacity heatmap for next 30 days
    data['capacity_heatmap'] = generate_capacity_heatmap(detailed_tasks, team_capacity_config)

    # Generate 6-month capacity timeline
    data['six_month_timeline'] = generate_6month_timeline(detailed_tasks, team_capacity_config)

    # Fetch upcoming shoots from Asana
    data['upcoming_shoots'] = []
    if ASANA_PAT:
        try:
            FILM_DATE_FIELD_GID = os.getenv('FILM_DATE_FIELD_GID')
            if FILM_DATE_FIELD_GID:
                upcoming_shoots = []
                now = datetime.now(timezone.utc)

                # Search for tasks with Film Date set across all production projects
                for project_name, project_gid in project_gids.items():
                    endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
                    params = {
                        'opt_fields': 'gid,name,custom_fields,start_on,due_on'
                    }

                    response = requests.get(endpoint, headers=headers, params=params)

                    if response.status_code == 200:
                        tasks = response.json().get('data', [])

                        for task in tasks:
                            # Find Film Date custom field
                            for field in task.get('custom_fields', []):
                                if field.get('gid') == FILM_DATE_FIELD_GID:
                                    date_value = field.get('date_value')
                                    if date_value:
                                        # Handle both date_time and date formats
                                        film_datetime_str = date_value.get('date_time') or date_value.get('date')
                                        if film_datetime_str:
                                            # Parse the datetime or date
                                            if 'T' in film_datetime_str or 'Z' in film_datetime_str:
                                                # Full datetime
                                                film_datetime = datetime.fromisoformat(film_datetime_str.replace('Z', '+00:00'))
                                            else:
                                                # Date only - set to start of day in UTC
                                                from datetime import date as date_type
                                                date_obj = date_type.fromisoformat(film_datetime_str)
                                                film_datetime = datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=timezone.utc)

                                            # Only include future shoots
                                            if film_datetime >= now:
                                                # Parse start_on and due_on if available
                                                start_date = None
                                                due_date = None
                                                if task.get('start_on'):
                                                    start_date = datetime.strptime(task['start_on'], '%Y-%m-%d').date()
                                                if task.get('due_on'):
                                                    due_date = datetime.strptime(task['due_on'], '%Y-%m-%d').date()

                                                # Clean task name - remove checkboxes
                                                task_name = task.get('name', 'Untitled')
                                                task_name = task_name.replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()

                                                upcoming_shoots.append({
                                                    'name': task_name,
                                                    'datetime': film_datetime,
                                                    'start_on': start_date,
                                                    'due_on': due_date,
                                                    'project': project_name,
                                                    'gid': task.get('gid')
                                                })
                                        break

                # Sort by datetime (earliest first) and limit to 10
                upcoming_shoots.sort(key=lambda x: x['datetime'])
                data['upcoming_shoots'] = upcoming_shoots[:10]
        except Exception as e:
            print(f"Warning: Could not fetch upcoming shoots: {e}")

    # Fetch upcoming project deadlines (due within next 10 days)
    data['upcoming_deadlines'] = []
    if ASANA_PAT:
        try:
            upcoming_deadlines = []
            now = datetime.now(timezone.utc).date()
            cutoff_date = now + timedelta(days=10)

            # Search for tasks with due dates across all production projects
            for project_name, project_gid in project_gids.items():
                endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
                params = {
                    'opt_fields': 'gid,name,start_on,due_on,due_at,completed'
                }

                response = requests.get(endpoint, headers=headers, params=params)

                if response.status_code == 200:
                    tasks = response.json().get('data', [])

                    for task in tasks:
                        if task.get('completed', False):
                            continue

                        # Extract due date (can be due_on or due_at)
                        due_date = None
                        if task.get('due_on'):
                            due_date = datetime.strptime(task['due_on'], '%Y-%m-%d').date()
                        elif task.get('due_at'):
                            due_datetime = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))
                            due_date = due_datetime.date()

                        # Only include if due within next 10 days
                        if due_date and now <= due_date <= cutoff_date:
                            days_until = (due_date - now).days

                            # Parse start_on if available
                            start_date = None
                            if task.get('start_on'):
                                start_date = datetime.strptime(task['start_on'], '%Y-%m-%d').date()

                            # Clean task name - remove checkboxes
                            task_name = task.get('name', 'Untitled')
                            task_name = task_name.replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()

                            upcoming_deadlines.append({
                                'name': task_name,
                                'start_on': start_date,
                                'due_date': due_date,
                                'days_until': days_until,
                                'project': project_name,
                                'gid': task.get('gid')
                            })

            # Sort by due date (earliest first)
            upcoming_deadlines.sort(key=lambda x: x['due_date'])
            data['upcoming_deadlines'] = upcoming_deadlines
        except Exception as e:
            print(f"Warning: Could not fetch upcoming deadlines: {e}")

    # Fetch forecasted projects from the Forecast project
    data['forecasted_projects'] = []
    if ASANA_PAT:
        try:
            forecasted_projects = []
            forecast_project_gid = '1212059678473189'

            endpoint = f"https://app.asana.com/api/1.0/projects/{forecast_project_gid}/tasks"
            params = {
                'opt_fields': 'gid,name,start_on,due_on,due_at,completed,notes'
            }

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                tasks = response.json().get('data', [])

                for task in tasks:
                    if task.get('completed', False):
                        continue

                    # Extract due date (can be due_on or due_at)
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

                    # Clean task name - remove checkboxes
                    task_name = task.get('name', 'Untitled')
                    task_name = task_name.replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()

                    forecasted_projects.append({
                        'name': task_name,
                        'start_on': start_date,
                        'due_date': due_date,
                        'notes': task.get('notes', ''),
                        'gid': task.get('gid')
                    })

                # Sort by due date if available, otherwise by start date
                forecasted_projects.sort(key=lambda x: (x['due_date'] or datetime.max.date(), x['start_on'] or datetime.max.date()))
                data['forecasted_projects'] = forecasted_projects
        except Exception as e:
            print(f"Warning: Could not fetch forecasted projects: {e}")

    return data

def fetch_detailed_tasks():
    """Fetch detailed task information from Asana for advanced analytics"""
    import requests
    from dotenv import load_dotenv

    load_dotenv(".env")

    ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
    if not ASANA_PAT:
        return []

    headers = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

    project_gids = {
        'Preproduction': '1208336083003480',
        'Production': '1209597979075357',
        'Post Production': '1209581743268502',
        'Forecast': '1212059678473189'
    }

    PERCENT_ALLOCATION_FIELD_GID = '1208923995383367'
    ACTUAL_ALLOCATION_FIELD_GID = '1212060330747288'
    TASK_PROGRESS_FIELD_GID = '1209598240843051'
    VIDEOGRAPHER_FIELD_GID = '1209693890455555'

    all_tasks = []

    for project_name, project_gid in project_gids.items():
        try:
            endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks"
            params = {
                'opt_fields': 'gid,name,completed,created_at,start_on,due_on,assignee.name,custom_fields'
            }

            response = requests.get(endpoint, headers=headers, params=params)
            if response.status_code == 200:
                tasks = response.json().get('data', [])

                for task in tasks:
                    # Extract allocation fields and task progress
                    estimated_allocation = 0
                    actual_allocation = 0
                    task_progress = None
                    videographer = None

                    if 'custom_fields' in task:
                        for field in task['custom_fields']:
                            if field['gid'] == PERCENT_ALLOCATION_FIELD_GID and field.get('number_value'):
                                estimated_allocation = field.get('number_value', 0) * 100
                            elif field['gid'] == ACTUAL_ALLOCATION_FIELD_GID and field.get('number_value'):
                                actual_allocation = field.get('number_value', 0) * 100
                            elif field['gid'] == TASK_PROGRESS_FIELD_GID:
                                # Task Progress is an enum field, get the display_value
                                if field.get('display_value'):
                                    task_progress = field.get('display_value')
                            elif field['gid'] == VIDEOGRAPHER_FIELD_GID:
                                # Videographer is a text field
                                videographer = field.get('text_value')

                    task_info = {
                        'gid': task.get('gid'),
                        'name': task.get('name', 'Untitled'),
                        'project': project_name,
                        'completed': task.get('completed', False),
                        'created_at': task.get('created_at'),
                        'start_on': task.get('start_on'),
                        'due_on': task.get('due_on'),
                        'assignee': task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned',
                        'estimated_allocation': estimated_allocation,
                        'actual_allocation': actual_allocation,
                        'task_progress': task_progress,
                        'videographer': videographer
                    }

                    all_tasks.append(task_info)
        except Exception as e:
            print(f"Warning: Could not fetch tasks from {project_name}: {e}")
            continue

    return all_tasks

def calculate_workload_forecast(tasks, team_capacity_config):
    """Calculate upcoming workload for 7, 14, and 30 day windows - matches heatmap/timeline logic"""
    today = datetime.now().date()
    DEFAULT_TASK_DURATION_DAYS = 30

    # Calculate daily team capacity (matches heatmap calculation)
    daily_max = sum(team_capacity_config[member]['max'] for member in team_capacity_config) / 5

    windows = {
        '7_days': {'days': 7, 'end': today + timedelta(days=7)},
        '14_days': {'days': 14, 'end': today + timedelta(days=14)},
        '30_days': {'days': 30, 'end': today + timedelta(days=30)}
    }

    # First pass: Calculate utilizations for all windows and find peak
    all_utilizations = []
    for window_name, window_info in windows.items():
        daily_utilizations = []
        active_task_set = set()  # Track unique tasks active in this window

        # Check each day in the window
        for day_offset in range(window_info['days']):
            current_date = today + timedelta(days=day_offset)
            daily_capacity = 0

            for task in tasks:
                if task['completed']:
                    continue

                try:
                    # Match heatmap logic for handling missing dates
                    if task['due_on']:
                        due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']
                        if task['start_on']:
                            start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                        else:
                            # Has due but no start: work backwards from due date
                            start_date = max(today, due_date - timedelta(days=DEFAULT_TASK_DURATION_DAYS))
                    elif task['start_on']:
                        # Has start but no due: assign default duration from start
                        start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                        due_date = start_date + timedelta(days=DEFAULT_TASK_DURATION_DAYS)
                    else:
                        # Neither date exists: assign defaults
                        start_date = today
                        due_date = today + timedelta(days=DEFAULT_TASK_DURATION_DAYS)

                    # Check if task is active on this specific day (matches heatmap logic)
                    if start_date <= current_date <= due_date:
                        # Divide by 5 for daily workload (5-day work week) - matches heatmap
                        daily_workload = task['estimated_allocation'] / 5
                        daily_capacity += daily_workload
                        # Track task as active in this window
                        active_task_set.add(task.get('gid', task.get('name', '')))
                except:
                    pass

            # Calculate utilization for this day
            day_utilization = (daily_capacity / daily_max * 100) if daily_max > 0 else 0
            daily_utilizations.append(day_utilization)
            all_utilizations.append(day_utilization)

        # Average the daily utilizations for the window (matches timeline logic)
        window_info['utilization'] = sum(daily_utilizations) / len(daily_utilizations) if daily_utilizations else 0
        window_info['tasks'] = len(active_task_set)
        window_info['daily_utilizations'] = daily_utilizations

    # Calculate adaptive thresholds for relative context
    peak_utilization = max(all_utilizations) if all_utilizations else 0
    adaptive_vmax = max(peak_utilization * 1.5, 20)
    adaptive_threshold_low = adaptive_vmax * 0.35
    adaptive_threshold_medium = adaptive_vmax * 0.60
    adaptive_threshold_high = adaptive_vmax * 0.80

    # Fixed thresholds for absolute capacity status
    FIXED_THRESHOLD_BUSY = 70
    FIXED_THRESHOLD_OVER = 100

    for window_name, window_info in windows.items():
        utilization = window_info['utilization']

        # Use FIXED thresholds for status (absolute capacity)
        if utilization >= FIXED_THRESHOLD_OVER:
            window_info['status'] = 'over'
        elif utilization >= FIXED_THRESHOLD_BUSY:
            window_info['status'] = 'busy'
        else:
            window_info['status'] = 'good'

        # Add relative workload context note
        relative_note = None
        if utilization >= adaptive_threshold_high:
            relative_note = "Peak workload period"
        elif utilization >= adaptive_threshold_medium:
            relative_note = "Higher than average workload"
        elif utilization >= adaptive_threshold_low:
            relative_note = "Moderate workload period"

        window_info['relative_note'] = relative_note

    return windows

def generate_6month_timeline(tasks, team_capacity_config):
    """Generate 6-month capacity timeline showing weekly utilization"""
    today = datetime.now().date()
    DEFAULT_TASK_DURATION_DAYS = 30

    # Calculate daily team capacity (matches heatmap calculation)
    daily_max = sum(team_capacity_config[member]['max'] for member in team_capacity_config) / 5

    # Generate 26 weeks (6 months)
    weeks = []
    for week_num in range(26):
        week_start = today + timedelta(weeks=week_num)
        week_end = week_start + timedelta(days=6)

        # Calculate average daily capacity for this week by checking each day
        daily_utilizations = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            daily_capacity = 0

            for task in tasks:
                if task['completed']:
                    continue

                try:
                    # Determine task date range (same logic as heatmap)
                    if task['due_on']:
                        due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']
                        if task['start_on']:
                            start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                        else:
                            start_date = max(today, due_date - timedelta(days=DEFAULT_TASK_DURATION_DAYS))
                    elif task['start_on']:
                        start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                        due_date = start_date + timedelta(days=DEFAULT_TASK_DURATION_DAYS)
                    else:
                        start_date = today
                        due_date = today + timedelta(days=DEFAULT_TASK_DURATION_DAYS)

                    # Check if task is active on this specific day
                    if start_date <= current_date <= due_date:
                        daily_workload = task['estimated_allocation'] / 5
                        daily_capacity += daily_workload
                except:
                    pass

            # Calculate utilization for this day
            day_utilization = (daily_capacity / daily_max * 100) if daily_max > 0 else 0
            daily_utilizations.append(day_utilization)

        # Average the daily utilizations for the week
        utilization = sum(daily_utilizations) / len(daily_utilizations) if daily_utilizations else 0

        # Count unique tasks active during this week
        task_count = 0
        for task in tasks:
            if task['completed']:
                continue
            try:
                if task['due_on']:
                    due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']
                    if task['start_on']:
                        start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                    else:
                        start_date = max(today, due_date - timedelta(days=DEFAULT_TASK_DURATION_DAYS))
                elif task['start_on']:
                    start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                    due_date = start_date + timedelta(days=DEFAULT_TASK_DURATION_DAYS)
                else:
                    start_date = today
                    due_date = today + timedelta(days=DEFAULT_TASK_DURATION_DAYS)

                if start_date <= week_end and due_date >= week_start:
                    task_count += 1
            except:
                pass

        weeks.append({
            'week_num': week_num + 1,
            'start_date': week_start.strftime('%Y-%m-%d'),
            'end_date': week_end.strftime('%Y-%m-%d'),
            'month': week_start.strftime('%b'),
            'task_count': task_count,
            'utilization': utilization,
            'status': None  # Will be set after calculating adaptive thresholds
        })

    # Calculate adaptive color thresholds (same logic as heatmap)
    utilization_values = [week['utilization'] for week in weeks]
    peak_utilization = max(utilization_values) if utilization_values else 0
    adaptive_vmax = max(peak_utilization * 1.5, 20)

    # Set adaptive thresholds
    threshold_low = adaptive_vmax * 0.35        # 35% of scale
    threshold_medium = adaptive_vmax * 0.60     # 60% of scale
    threshold_high = adaptive_vmax * 0.80       # 80% of scale

    # Apply adaptive status to each week
    for week in weeks:
        utilization = week['utilization']
        if utilization < threshold_low:
            week['status'] = 'good'
        elif utilization < threshold_medium:
            week['status'] = 'busy'
        elif utilization < threshold_high:
            week['status'] = 'warning'
        else:
            week['status'] = 'over'

    return weeks

def identify_at_risk_tasks(tasks, team_capacity):
    """Identify tasks that are at risk of missing deadlines based on Task Progress and project type"""
    at_risk = []
    today = datetime.now().date()
    seven_days = today + timedelta(days=7)

    for task in tasks:
        if task['completed']:
            continue

        risk_factors = []
        task_progress = task.get('task_progress')
        project = task.get('project')

        # Check if task was recently updated (indicates active work)
        task_modified = task.get('modified_at')
        recently_updated = False
        if task_modified:
            try:
                if isinstance(task_modified, str):
                    modified_date = datetime.fromisoformat(task_modified.replace('Z', '+00:00')).date()
                else:
                    modified_date = task_modified.date() if hasattr(task_modified, 'date') else task_modified

                # If task was updated in last 3 days, consider it actively being worked on
                recently_updated = (today - modified_date).days <= 3
            except:
                recently_updated = False

        # Check if task is overdue
        if task['due_on']:
            try:
                due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']

                if due_date < today:
                    risk_factors.append(f"Overdue by {(today - due_date).days} days")
                elif due_date <= seven_days:
                    # Due within 7 days - check Task Progress based on project type
                    # IMPORTANT: Only flag as at-risk if task hasn't been properly updated

                    if project == 'Production':
                        # Production: at-risk if "Needs Scheduling" and approaching due date
                        # BUT NOT if it's already "In Progress" or "Complete"
                        if task_progress == 'Needs Scheduling':
                            risk_factors.append(f"Due in {(due_date - today).days} days, needs scheduling")

                    elif project == 'Post Production':
                        # Post Production: at-risk if "Filmed" or "Offloaded" (but NOT "In Progress" or "Complete") and approaching due date
                        # KEY FIX: Exclude tasks that are "In Progress" or "Complete" - they're actively being worked on
                        if task_progress in ['Filmed', 'Offloaded'] and task_progress not in ['In Progress', 'Complete']:
                            risk_factors.append(f"Due in {(due_date - today).days} days, not yet in progress")

                    # Additional check: Don't flag tasks that are actively "In Progress" regardless of project type
                    if task_progress == 'In Progress':
                        # Remove any risk factors already added - task is actively being worked on
                        risk_factors = []

                    # Don't flag tasks that were recently updated - indicates active attention
                    if recently_updated:
                        # Remove any risk factors - task has recent activity
                        risk_factors = []
            except:
                pass

        # Check if running over estimate
        if task['estimated_allocation'] > 0 and task['actual_allocation'] > 0:
            variance = ((task['actual_allocation'] - task['estimated_allocation']) / task['estimated_allocation']) * 100
            if variance > 20:
                risk_factors.append(f"Over estimate by {variance:.0f}%")

        if risk_factors:
            assignee = task['assignee']
            videographer = task.get('videographer', 'N/A')
            at_risk.append({
                'name': task['name'],
                'project': task['project'],
                'assignee': assignee,
                'videographer': videographer,
                'due_on': task.get('due_on', 'No due date'),
                'risks': risk_factors
            })

    return at_risk

def generate_capacity_heatmap(tasks, team_capacity_config):
    """Generate capacity utilization heatmap for next 30 days with adaptive color scaling"""
    today = datetime.now().date()
    heatmap_data = []

    # Default span for tasks without dates (matches video_scorer.py CONFIG)
    DEFAULT_TASK_DURATION_DAYS = 30

    # Match PNG heatmap: MAX_CAPACITY/5 for daily capacity (5-day work week)
    daily_max = sum(team_capacity_config[member]['max'] for member in team_capacity_config) / 5

    # First pass: calculate all utilization values to find the peak
    utilization_values = []

    # Generate next 30 days
    for day_offset in range(30):
        current_date = today + timedelta(days=day_offset)
        daily_capacity = 0

        # Calculate capacity needed for tasks active on this day (excluding completed to match PNG)
        for task in tasks:
            # Skip completed tasks to match video_scorer.py behavior
            if task.get('completed', False):
                continue

            try:
                # Match video_scorer.py logic for handling missing dates
                if task['due_on']:
                    due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']

                    if task['start_on']:
                        start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                    else:
                        # Has due but no start: work backwards from due date
                        calculated_start = due_date - timedelta(days=DEFAULT_TASK_DURATION_DAYS)
                        start_date = max(today, calculated_start)

                elif task['start_on']:
                    # Has start but no due: assign default duration from start
                    start_date = datetime.fromisoformat(task['start_on']).date() if isinstance(task['start_on'], str) else task['start_on']
                    due_date = start_date + timedelta(days=DEFAULT_TASK_DURATION_DAYS)

                else:
                    # Neither date exists: assign defaults (matches video_scorer.py lines 700-703)
                    start_date = today
                    due_date = today + timedelta(days=DEFAULT_TASK_DURATION_DAYS)

                # Only count if this date falls within the task's work period
                if start_date <= current_date <= due_date:
                    # Use SAME calculation as PNG heatmap for consistency
                    # allocation% / 5 = daily workload (5-day work week)
                    daily_workload = task['estimated_allocation'] / 5

                    # Add to total daily capacity requirement
                    daily_capacity += daily_workload
            except Exception as e:
                pass

        # Calculate utilization as percentage of daily team capacity
        utilization = (daily_capacity / daily_max * 100) if daily_max > 0 else 0
        utilization_values.append(utilization)

    # Calculate adaptive vmax using SAME formula as PNG heatmap
    # video_scorer.py line 863: adaptive_vmax = max(phase_peak * 1.5, 20)
    peak_utilization = max(utilization_values) if utilization_values else 0
    adaptive_vmax = max(peak_utilization * 1.5, 20)

    # Second pass: categorize with adaptive thresholds
    for day_offset in range(30):
        current_date = today + timedelta(days=day_offset)
        utilization = utilization_values[day_offset]

        # Use adaptive color scaling matching PNG heatmap with more granular colors
        # Scale is 0 to adaptive_vmax, divided into 5 color bands for better visualization
        threshold_very_low = adaptive_vmax * 0.15   # 15% of scale
        threshold_low = adaptive_vmax * 0.35        # 35% of scale
        threshold_medium = adaptive_vmax * 0.60     # 60% of scale
        threshold_high = adaptive_vmax * 0.80       # 80% of scale

        if utilization < threshold_very_low:
            status = 'very_low'    # Light green
        elif utilization < threshold_low:
            status = 'low'         # Green
        elif utilization < threshold_medium:
            status = 'medium'      # Yellow-green
        elif utilization < threshold_high:
            status = 'high'        # Orange
        else:
            status = 'very_high'   # Red

        heatmap_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': current_date.strftime('%a'),
            'utilization': utilization,
            'status': status
        })

    return heatmap_data

def generate_html_dashboard(data):
    """Generate interactive HTML dashboard"""

    # Extract key metrics
    total_tasks = data.get('active_task_count', 0)

    # Category metrics (cumulative)
    category_data = []
    tracking_period = ""
    if data['variance'] is not None:
        for _, row in data['variance'].iterrows():
            category_data.append({
                'name': row['Category'],
                'actual': float(row['Actual %']),
                'target': float(row['Target %']),
                'variance': float(row['Variance'])
            })

        # Calculate tracking period from history
        if data.get('variance_history') is not None and not data['variance_history'].empty:
            dates = pd.to_datetime(data['variance_history']['Date'])
            start_date = dates.min().strftime('%b %d, %Y')
            end_date = dates.max().strftime('%b %d, %Y')
            days_tracked = (dates.max() - dates.min()).days + 1
            tracking_period = f"{start_date} - {end_date} ({days_tracked} days)"

    # Delivery metrics
    delivery_metrics = {
        'total_completed': 0,
        'completed_this_year': 0,
        'on_time_rate': 0,
        'avg_capacity_variance': 0,
        'projects_delayed_capacity': 0,
        'avg_days_variance': 0
    }

    if data['delivery_log'] is not None:
        df = data['delivery_log']
        delivery_metrics['total_completed'] = len(df)

        # Calculate projects completed this year
        current_year = datetime.now().year
        tasks_with_completion_date = df[df['Completed Date'].notna()]
        completed_this_year = 0
        for _, task in tasks_with_completion_date.iterrows():
            try:
                # Parse completion date (format: YYYY-MM-DD)
                completion_date = pd.to_datetime(task['Completed Date'])
                if completion_date.year == current_year:
                    completed_this_year += 1
            except (ValueError, TypeError):
                pass
        delivery_metrics['completed_this_year'] = completed_this_year

        # On-time completion rate (only count tasks with due dates)
        # Filter out tasks where Delivery Status is null/NaN (no due date)
        tasks_with_due_dates = df[df['Delivery Status'].notna()]
        on_time = len(tasks_with_due_dates[tasks_with_due_dates['Delivery Status'].isin(['On Time', 'Early'])])
        tasks_with_due_dates_count = len(tasks_with_due_dates)
        delivery_metrics['on_time_rate'] = (on_time / tasks_with_due_dates_count * 100) if tasks_with_due_dates_count > 0 else 0

        # Calculate avg days variance
        numeric_variance = df[df['Days Variance'] != 'N/A']['Days Variance']
        if len(numeric_variance) > 0:
            delivery_metrics['avg_days_variance'] = numeric_variance.mean()

        # Average capacity variance (allocation variance)
        tasks_with_actual = df[df['Actual Allocation %'] != 'N/A']
        if len(tasks_with_actual) > 0:
            # Calculate variance for each task with actual data
            variances = []
            for _, task in tasks_with_actual.iterrows():
                try:
                    estimated = float(task['Estimated Allocation %'])
                    actual = float(task['Actual Allocation %'])
                    variance_pct = ((actual - estimated) / estimated * 100) if estimated > 0 else 0
                    variances.append(variance_pct)
                except (ValueError, TypeError):
                    continue

            if variances:
                delivery_metrics['avg_capacity_variance'] = sum(variances) / len(variances)

        # Projects delayed due to capacity (late + over allocation)
        delayed_capacity = 0
        for _, task in df.iterrows():
            is_late = task['Delivery Status'] == 'Late'
            allocation_over = False

            if task['Allocation Variance %'] != 'N/A':
                try:
                    alloc_var = float(task['Allocation Variance %'])
                    allocation_over = alloc_var > 10  # More than 10% over estimate
                except (ValueError, TypeError):
                    pass

            if is_late and allocation_over:
                delayed_capacity += 1

        delivery_metrics['projects_delayed_capacity'] = delayed_capacity

    # Get team capacity from data (calculated in read_reports)
    team_capacity = data['team_capacity']

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perimeter Studio Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        /* ===== CSS VARIABLES FOR THEME SYSTEM ===== */
        :root {{
            /* Light Theme Colors */
            --bg-primary: #f8f9fa;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e9ecef;

            --text-primary: #09243F;
            --text-secondary: #6c757d;
            --text-muted: #adb5bd;

            --brand-primary: #60BBE9;
            --brand-secondary: #09243F;
            --brand-accent: #60BBE9;

            --border-color: #dee2e6;
            --border-accent: #60BBE9;

            --shadow-light: rgba(0, 0, 0, 0.1);
            --shadow-medium: rgba(0, 0, 0, 0.15);

            /* Status Colors */
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;

            /* Chart Colors */
            --chart-bg: #e9ecef;
            --chart-progress: var(--brand-primary);

            /* Interactive Elements */
            --hover-bg: rgba(96, 187, 233, 0.1);
            --active-bg: rgba(96, 187, 233, 0.2);

            /* Mobile Breakpoints */
            --mobile-breakpoint: 768px;
            --tablet-breakpoint: 1024px;
        }}

        /* Dark Theme */
        :root[data-theme="dark"] {{
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #404040;

            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-muted: #808080;

            --brand-primary: #60BBE9;
            --brand-secondary: #4a9cd9;
            --brand-accent: #7ac3ed;

            --border-color: #404040;
            --border-accent: #60BBE9;

            --shadow-light: rgba(255, 255, 255, 0.1);
            --shadow-medium: rgba(255, 255, 255, 0.15);

            --chart-bg: #404040;
            --chart-progress: var(--brand-primary);

            --hover-bg: rgba(96, 187, 233, 0.2);
            --active-bg: rgba(96, 187, 233, 0.3);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
            scroll-padding-top: 80px;
        }}

        /* Section anchor targets */
        #overview, #capacity, #metrics, #deadlines, #forecasts, #analytics {{
            scroll-margin-top: 80px;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            min-height: 100vh;
            overflow-x: hidden;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}

        /* ===== STICKY NAVIGATION ===== */
        .sticky-nav {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 0;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px var(--shadow-light);
            backdrop-filter: blur(8px);
            margin-left: -20px;
            margin-right: -20px;
            margin-top: -20px;
        }}

        .nav-container {{
            max-width: 95%;
            margin: 0 auto;
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            padding: 0 20px;
        }}

        .nav-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 6px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}

        .nav-link:hover {{
            color: var(--brand-primary);
            background: var(--hover-bg);
            transform: translateY(-1px);
        }}

        .nav-link:focus {{
            outline: 2px solid var(--brand-primary);
            outline-offset: 2px;
        }}

        .nav-link.active {{
            color: var(--brand-primary);
            background: var(--active-bg);
            font-weight: 600;
        }}

        .dashboard-container {{
            max-width: 95%;
            margin: 0 auto;
            overflow-x: hidden;
        }}

        .header {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px var(--shadow-light);
            margin-bottom: 40px;
            border-left: 4px solid var(--border-accent);
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }}

        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
        }}

        .header-text {{
            flex: 1;
            text-align: center;
        }}

        /* Theme Toggle Button */
        .theme-toggle {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .theme-toggle:hover {{
            background: var(--hover-bg);
            border-color: var(--brand-primary);
        }}

        .theme-toggle:active {{
            background: var(--active-bg);
        }}

        .theme-icon {{
            font-size: 16px;
            line-height: 1;
        }}


        .export-btn {{
            background: var(--brand-primary);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }}

        .export-btn:hover {{
            background: var(--brand-secondary);
            transform: translateY(-1px);
            box-shadow: 0 2px 4px var(--shadow-medium);
        }}

        .export-btn:active {{
            transform: translateY(0);
        }}

        .export-btn:focus {{
            outline: 2px solid var(--brand-accent);
            outline-offset: 2px;
        }}

        /* ===== ACCESSIBILITY IMPROVEMENTS ===== */
        /* Focus management for keyboard navigation */
        .theme-toggle:focus {{
            outline: 2px solid var(--brand-primary);
            outline-offset: 2px;
        }}

        /* High contrast mode support */
        @media (prefers-contrast: high) {{
            :root {{
                --shadow-light: rgba(0, 0, 0, 0.3);
                --shadow-medium: rgba(0, 0, 0, 0.4);
            }}

            .header {{
                border-left-width: 6px;
            }}
        }}

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }}
        }}

        /* Screen reader only text */
        .sr-only {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}

        /* Focus indicators for interactive elements */
        .card:focus-within {{
            box-shadow: 0 0 0 2px var(--brand-primary);
        }}

        .progress-ring:focus {{
            outline: 2px solid var(--brand-primary);
            outline-offset: 2px;
        }}

        /* Improved color contrast for text */
        .metric-value {{
            font-weight: 700;
            color: var(--text-primary);
        }}

        .metric-label {{
            color: var(--text-secondary);
            font-weight: 500;
        }}

        /* ===== MOBILE RESPONSIVE DESIGN ===== */
        /* Tablet breakpoint */
        @media (max-width: 1024px) {{
            .dashboard-container {{
                max-width: 98%;
                margin: 0 auto;
            }}

            .header {{
                padding: 20px;
            }}

            .header h1 {{
                font-size: 28px;
            }}

            .theme-toggle {{
                padding: 10px 16px;
                font-size: 13px;
                /* Ensure minimum touch target of 44x44px for accessibility */
                min-height: 44px;
            }}

            .grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}

            .card {{
                padding: 20px;
            }}

            .card h2 {{
                font-size: 20px;
                margin-bottom: 15px;
            }}

            .progress-rings-container {{
                gap: 15px;
            }}

            .team-member {{
                margin-bottom: 15px;
            }}
        }}

        /* Mobile breakpoint */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header {{
                padding: 15px;
            }}

            .header h1 {{
                font-size: 24px;
                margin-bottom: 8px;
            }}

            .subtitle {{
                font-size: 14px;
                margin-bottom: 10px;
            }}

            .timestamp {{
                font-size: 12px;
            }}

            .header {{
                display: grid;
                grid-template-areas:
                    "title"
                    "subtitle"
                    "timestamp"
                    "controls";
                grid-template-rows: auto auto auto auto;
                gap: 15px;
                position: relative;
                padding: 20px 15px; /* Normal padding */
            }}

            .header-controls {{
                grid-area: controls;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: row;
                flex-wrap: wrap;
                gap: 12px;
                z-index: 10;
            }}

            .header h1 {{
                grid-area: title;
                font-size: 24px;
                margin: 0;
            }}

            .header .subtitle {{
                grid-area: subtitle;
                margin: 0;
            }}

            .header .timestamp {{
                grid-area: timestamp;
                margin: 0;
            }}

            .theme-toggle {{
                flex: none;
            }}

            .export-controls {{
                display: flex;
                flex-direction: row;
                margin-top: 0;
                gap: 8px;
            }}

            .export-btn {{
                font-size: 12px;
                padding: 8px 14px;
                /* Ensure minimum touch target of 44x44px for accessibility */
                min-height: 44px;
                min-width: 44px;
                border-radius: 22px;
            }}

            .card {{
                padding: 15px;
            }}

            .card h2 {{
                font-size: 18px;
                margin-bottom: 12px;
            }}

            .metric {{
                margin-bottom: 15px;
                flex-direction: column;
                align-items: flex-start;
                text-align: left;
            }}

            .metric-label {{
                font-size: 14px;
                margin-bottom: 5px;
            }}

            .metric-value {{
                font-size: 24px;
            }}

            /* Mobile-friendly team capacity */
            .team-member {{
                margin-bottom: 20px;
                padding: 15px;
                background: var(--bg-tertiary);
                border-radius: 8px;
            }}

            .team-member-name {{
                font-size: 16px;
                margin-bottom: 8px;
            }}

            .team-member-capacity {{
                font-size: 14px;
                margin-bottom: 10px;
            }}

            .progress-bar {{
                height: 25px;
            }}

            .progress-fill {{
                font-size: 14px;
                line-height: 25px;
            }}

            /* Mobile charts */
            .chart-container {{
                height: 250px;
                margin: 10px 0;
            }}

            .velocity-container {{
                height: 250px;
                margin: 10px 0;
            }}

            /* Specific fixes for Historical Capacity chart only */
            #capacityHistoryChart {{
                display: block !important;
                width: 100% !important;
                height: 250px !important;
                min-width: 200px !important;
                visibility: visible !important;
            }}

            .progress-rings-container {{
                flex-direction: column;
                align-items: center;
                gap: 20px;
            }}

            .progress-ring {{
                margin-bottom: 15px;
            }}

            .gauge-container {{
                width: 150px;
                height: 150px;
            }}

            /* Mobile timeline adjustments */
            .timeline-container {{
                overflow-x: auto;
                padding-bottom: 10px;
            }}

            .timeline-row {{
                min-width: 600px;
            }}

            .timeline-project-col,
            .timeline-project-name {{
                min-width: 120px;
                width: 120px;
            }}

            /* Enhanced horizontal scroll for mobile */
            @media (max-width: 768px) {{
                .timeline-container {{
                    overflow-x: auto;
                    -webkit-overflow-scrolling: touch;
                    scroll-snap-type: x proximity;
                    padding-bottom: 15px;
                    position: relative;
                }}

                /* Hide the vertical line on mobile */
                .timeline-container::before {{
                    display: none;
                }}

                /* Add scroll indicator */
                .timeline-container::after {{
                    content: '← Swipe to see timeline →';
                    position: sticky;
                    left: 50%;
                    transform: translateX(-50%);
                    bottom: 0;
                    background: rgba(52, 152, 219, 0.9);
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 500;
                    z-index: 20;
                    white-space: nowrap;
                    pointer-events: none;
                    opacity: 0.8;
                    animation: fadeInOut 3s ease-in-out infinite;
                }}

                @keyframes fadeInOut {{
                    0%, 100% {{ opacity: 0.6; }}
                    50% {{ opacity: 1; }}
                }}

                .timeline-header,
                .timeline-row {{
                    min-width: 700px;
                    display: flex;
                    align-items: center;
                }}

                .timeline-project-col,
                .timeline-project-name {{
                    min-width: 140px;
                    width: 140px;
                    position: sticky;
                    left: 0;
                    background: var(--bg-secondary);
                    z-index: 10;
                    border-right: 2px solid var(--border-color);
                    box-shadow: 2px 0 4px var(--shadow-light);
                    flex-shrink: 0;
                }}

                .timeline-dates,
                .timeline-bars {{
                    flex: 1;
                    min-width: 560px;
                }}

                .timeline-date {{
                    font-size: 10px;
                    scroll-snap-align: start;
                }}
            }}

            /* Small mobile optimizations */
            @media (max-width: 480px) {{
                .timeline-project-col,
                .timeline-project-name {{
                    font-size: 12px;
                    min-width: 100px;
                    width: 100px;
                }}

                .timeline-date {{
                    font-size: 9px;
                    padding: 0 2px;
                }}

                .timeline-bar {{
                    height: 28px;
                    font-size: 9px;
                }}

                .timeline-header,
                .timeline-row {{
                    min-width: 600px;
                }}

                .timeline-dates,
                .timeline-bars {{
                    min-width: 500px;
                }}
            }}

            /* Mobile table styles */
            table {{
                font-size: 14px;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}

            th, td {{
                padding: 8px 6px;
                white-space: nowrap;
            }}

            /* Add visual scroll indicator for tables */
            .card:has(table)::after {{
                content: '← Scroll →';
                position: absolute;
                bottom: 10px;
                right: 10px;
                font-size: 11px;
                color: var(--text-muted);
                opacity: 0.6;
                pointer-events: none;
            }}

            .at-risk-item {{
                padding: 12px;
                margin-bottom: 12px;
            }}

            .at-risk-item h4 {{
                font-size: 16px;
            }}

            .at-risk-item p {{
                font-size: 14px;
                line-height: 1.4;
            }}
        }}

        /* Small mobile breakpoint */
        @media (max-width: 480px) {{
            body {{
                padding: 8px;
            }}

            .header {{
                padding: 12px;
                padding-top: 80px;
            }}

            .header h1 {{
                font-size: 20px;
            }}

            .theme-toggle {{
                padding: 4px 8px;
                font-size: 12px;
            }}

            .card {{
                padding: 12px;
            }}

            .card h2 {{
                font-size: 16px;
            }}

            .metric-value {{
                font-size: 20px;
            }}

            .team-member {{
                padding: 12px;
            }}

            .progress-ring {{
                width: 100px;
                height: 100px;
            }}


            .progress-ring-value {{
                font-size: 16px;
            }}

            .progress-ring-label {{
                font-size: 9px;
            }}

            .gauge-container {{
                width: 120px;
                height: 120px;
            }}

            .gauge-value {{
                font-size: 32px;
            }}

            .chart-container {{
                height: 200px;
            }}

            /* Stack team capacity in single column */
            .team-capacity-grid {{
                grid-template-columns: 1fr !important;
            }}
        }}

        /* ===== INTERACTIVE FEATURES ===== */
        /* Tooltip styles */
        .tooltip {{
            position: relative;
            cursor: help;
        }}

        .tooltip::before {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: normal;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
            box-shadow: 0 2px 8px var(--shadow-medium);
            z-index: 1000;
            border: 1px solid var(--border-color);
            max-width: 250px;
            white-space: normal;
        }}

        .tooltip::after {{
            content: '';
            position: absolute;
            bottom: 116%;
            left: 50%;
            transform: translateX(-50%);
            border: 5px solid transparent;
            border-top-color: var(--bg-secondary);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}

        .tooltip:hover::before,
        .tooltip:hover::after {{
            opacity: 1;
            visibility: visible;
        }}

        /* Interactive card hover effects */
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow-medium);
        }}

        .team-member:hover {{
            background: var(--hover-bg);
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }}

        /* Sortable table styles */
        .sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
        }}

        .sortable:hover {{
            background: var(--hover-bg);
        }}

        .sortable::after {{
            content: '↕️';
            position: absolute;
            right: 8px;
            opacity: 0.5;
            font-size: 12px;
        }}

        .sortable.asc::after {{
            content: '↑';
            opacity: 1;
        }}

        .sortable.desc::after {{
            content: '↓';
            opacity: 1;
        }}

        /* Filter controls */
        .filter-controls {{
            margin: 15px 0;
            padding: 15px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}

        .filter-control {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .filter-control label {{
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
        }}

        .filter-control select,
        .filter-control input {{
            padding: 6px 8px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 14px;
        }}

        .filter-control select:focus,
        .filter-control input:focus {{
            outline: 2px solid var(--brand-primary);
            outline-offset: -2px;
        }}

        /* Quick stats hover effects */
        .metric:hover .metric-value {{
            color: var(--brand-primary);
            transition: color 0.3s ease;
        }}

        /* Interactive progress bars */
        .progress-bar:hover .progress-fill {{
            box-shadow: 0 0 10px rgba(96, 187, 233, 0.4);
            transition: box-shadow 0.3s ease;
        }}

        /* Mobile filter adjustments */
        @media (max-width: 768px) {{
            .filter-controls {{
                flex-direction: column;
                align-items: stretch;
            }}

            .filter-control {{
                justify-content: space-between;
            }}

            .filter-control select,
            .filter-control input {{
                min-width: 120px;
            }}
        }}

        /* ===== PROJECT CARDS (Shoots, Deadlines, Forecast) ===== */
        .project-card {{
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 18px;
            background: var(--bg-secondary);
            margin-bottom: 16px;
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}

        .project-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }}

        .project-card-date {{
            font-size: 16px;
            font-weight: bold;
            color: var(--text-primary);
        }}

        .project-card-time {{
            font-size: 20px;
            font-weight: 600;
            color: var(--brand-primary);
            margin-top: 4px;
        }}

        .project-card-badge {{
            display: inline-block;
            padding: 6px 12px;
            background: var(--brand-secondary);
            color: white;
            font-size: 14px;
            border-radius: 6px;
            white-space: nowrap;
        }}

        .project-card-title {{
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
            font-size: 16px;
            line-height: 1.4;
            display: block;
            margin-bottom: 8px;
        }}

        .project-card-title:hover {{
            color: var(--brand-primary);
        }}

        .project-card-details {{
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.4;
            margin-bottom: 8px;
        }}

        .project-card-meta {{
            color: var(--text-muted);
            font-size: 12px;
        }}

        /* Mobile project card optimizations */
        @media (max-width: 768px) {{
            .project-card {{
                padding: 14px;
                margin-bottom: 14px;
            }}

            .project-card-header {{
                flex-direction: column;
                gap: 8px;
            }}

            .project-card-date {{
                font-size: 15px;
            }}

            .project-card-time {{
                font-size: 18px;
            }}

            .project-card-badge {{
                padding: 5px 10px;
                font-size: 13px;
                align-self: flex-start;
            }}

            .project-card-title {{
                font-size: 15px;
                line-height: 1.5;
                /* Ensure touch targets are at least 44x44px */
                min-height: 44px;
                display: flex;
                align-items: center;
            }}
        }}

        @media (max-width: 480px) {{
            .project-card {{
                padding: 12px;
                margin-bottom: 12px;
            }}

            .project-card-date {{
                font-size: 14px;
            }}

            .project-card-time {{
                font-size: 16px;
            }}

            .project-card-title {{
                font-size: 14px;
            }}

            .project-card-details {{
                font-size: 13px;
            }}
        }}

        /* Task list and detail styles */
        .task-list-item {{
            font-size: 12px;
            color: var(--text-secondary);
            margin: 4px 0;
        }}

        .empty-state {{
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
        }}

        .success-state {{
            text-align: center;
            padding: 20px;
            color: var(--success-color);
        }}

        .task-name {{
            font-weight: bold;
            color: var(--brand-secondary);
        }}

        .task-detail {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 5px;
        }}

        .task-risk {{
            font-size: 13px;
            color: var(--danger-color);
            margin-top: 8px;
        }}

        .project-link {{
            color: var(--brand-primary);
            text-decoration: none;
            font-size: 14px;
        }}

        .project-link:hover {{
            text-decoration: underline;
        }}

        .section-description {{
            color: var(--text-secondary);
            margin-top: 8px;
            font-size: 14px;
        }}

        /* At-risk and external project sections */
        .at-risk-item {{
            border-left: 4px solid var(--danger-color);
            padding: 10px;
            margin-bottom: 10px;
            background: var(--bg-tertiary);
            border-radius: 4px;
        }}

        .external-project-item {{
            margin-top: 10px;
            padding-left: 10px;
            border-left: 2px solid var(--brand-primary);
        }}

        .project-task-name {{
            font-weight: bold;
            color: var(--text-primary);
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        /* ===== GAUGE CHART STYLES ===== */
        .gauge-container {{
            position: relative;
            width: 200px;
            height: 200px;
            margin: 20px auto;
        }}

        .gauge-svg {{
            transform: rotate(-90deg);
        }}

        .gauge-background {{
            fill: none;
            stroke: var(--chart-bg);
            stroke-width: 20;
        }}

        .gauge-progress {{
            fill: none;
            stroke-width: 20;
            stroke-linecap: round;
            transition: stroke-dashoffset 2s ease;
        }}

        .gauge-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .gauge-value {{
            font-size: 48px;
            font-weight: 700;
            color: var(--brand-primary);
        }}

        .gauge-label {{
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}

        /* ===== PROGRESS RING STYLES ===== */
        .progress-rings-container {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
            margin: 15px 0;
            padding: 15px;
        }}

        .progress-ring {{
            position: relative;
            width: 160px;
            height: 160px;
            text-align: center;
            display: inline-block;
        }}

        .progress-ring-svg {{
            transform: rotate(-90deg);
        }}

        .progress-ring-circle {{
            fill: none;
            stroke-width: 10;
            stroke-linecap: round;
        }}

        .progress-ring-bg {{
            stroke: var(--chart-bg);
        }}

        .progress-ring-progress {{
            transition: stroke-dashoffset 2s ease;
        }}

        .progress-ring-text {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            pointer-events: none;
        }}

        .progress-ring-value {{
            font-size: 22px;
            font-weight: 700;
            color: var(--text-primary);
            display: block;
            line-height: 1;
            margin: 0;
        }}

        .progress-ring-label {{
            font-size: 9px;
            color: var(--text-secondary);
            display: block;
            margin-top: 4px;
            line-height: 1.2;
            font-weight: 500;
            max-width: 100%;
            text-align: center;
        }}

        /* ===== TIMELINE GANTT STYLES ===== */
        .timeline-container {{
            margin: 15px 0;
            overflow: hidden;
            list-style: none !important;
            position: relative;
            padding-left: 0 !important;
        }}

        .timeline-container::before {{
            content: '';
            position: absolute;
            left: 25%;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--brand-secondary);
            z-index: 10;
        }}

        .timeline-container *,
        .timeline-container *::before,
        .timeline-container *::after {{
            list-style: none !important;
            list-style-type: none !important;
        }}

        .timeline-header {{
            display: flex;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--border-color);
        }}

        .timeline-project-col {{
            width: 25%;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 14px;
            padding-right: 12px;
            margin-right: 12px;
            flex-shrink: 0;
        }}

        .timeline-dates {{
            display: flex;
            flex: 1;
        }}

        .timeline-date {{
            flex: 1;
            text-align: center;
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .timeline-row {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            min-height: 32px;
            list-style: none !important;
            list-style-type: none !important;
        }}

        .timeline-row::before,
        .timeline-row::after,
        .timeline-row::marker {{
            display: none !important;
            content: none !important;
        }}

        .timeline-project-name {{
            width: 25%;
            font-size: 13px;
            color: var(--text-primary);
            padding-right: 12px;
            font-weight: 500;
            margin-right: 12px;
            flex-shrink: 0;
            line-height: 1.2;
            overflow: hidden;
            word-wrap: break-word;
        }}

        .timeline-project-name::before,
        .timeline-project-name::after,
        .timeline-project-name::marker {{
            display: none !important;
            content: '' !important;
        }}

        .timeline-bars {{
            display: flex;
            flex: 1;
            position: relative;
            height: 32px;
        }}

        .timeline-bar {{
            position: absolute;
            height: 24px;
            border-radius: 4px;
            background: var(--brand-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            font-weight: 600;
        }}

        .timeline-bar.critical {{
            background: #dc3545;
        }}

        .timeline-bar.warning {{
            background: #ffc107;
        }}

        .timeline-bar.normal {{
            background: var(--brand-primary);
        }}

        .timeline-bar.info {{
            background: #17a2b8;
        }}

        /* ===== RADAR/SPIDER CHART STYLES ===== */
        .radar-container {{
            position: relative;
            width: 100%;
            max-width: 600px;
            height: 600px;
            margin: 20px auto;
        }}

        @media (max-width: 768px) {{
            .radar-container {{
                height: 400px;
                max-width: 100%;
            }}

            .radar-container svg {{
                max-width: 100%;
                height: auto;
            }}
        }}

        @media (max-width: 480px) {{
            .radar-container {{
                height: 300px;
            }}

            .radar-label {{
                font-size: 10px !important;
            }}
        }}

        .radar-grid {{
            fill: none;
            stroke: var(--border-color);
            stroke-width: 1;
        }}

        .radar-axis {{
            stroke: var(--text-secondary);
            stroke-width: 1;
        }}

        .radar-area {{
            fill: rgba(96, 187, 233, 0.3);
            stroke: #60BBE9;
            stroke-width: 2;
        }}

        .radar-target {{
            fill: rgba(220, 53, 69, 0.2);
            stroke: #dc3545;
            stroke-width: 2;
            stroke-dasharray: 5, 5;
        }}

        .radar-label {{
            fill: var(--text-primary);
            font-size: 12px;
            font-weight: 600;
            text-anchor: middle;
        }}

        /* ===== SUNBURST CHART STYLES ===== */
        .sunburst-container {{
            position: relative;
            width: 100%;
            max-width: 400px;
            height: 400px;
            margin: 20px auto;
        }}

        @media (max-width: 768px) {{
            .sunburst-container {{
                height: 300px;
                max-width: 100%;
            }}

            .sunburst-container svg {{
                max-width: 100%;
                height: auto;
            }}
        }}

        @media (max-width: 480px) {{
            .sunburst-container {{
                height: 250px;
            }}

            .sunburst-text {{
                font-size: 9px !important;
            }}

            .sunburst-center-text {{
                font-size: 18px !important;
            }}
        }}

        .sunburst-slice {{
            cursor: pointer;
            transition: opacity 0.2s;
            stroke: white;
            stroke-width: 2;
        }}

        .sunburst-slice:hover {{
            opacity: 0.8;
        }}

        .sunburst-text {{
            fill: white;
            font-size: 11px;
            font-weight: 600;
            pointer-events: none;
        }}

        .sunburst-center-text {{
            fill: #60BBE9;
            font-size: 24px;
            font-weight: 700;
            text-anchor: middle;
        }}

        /* ===== VELOCITY TREND CHART ===== */
        .velocity-container {{
            position: relative;
            height: 280px;
            margin-top: 12px;
            max-width: 100%;
            overflow: hidden;
        }}

        /* ===== HEAT MAP CALENDAR STYLES ===== */
        .heatmap-calendar {{
            display: grid;
            grid-template-columns: auto repeat(10, 1fr);
            gap: 4px;
            margin: 20px 0;
            overflow-x: auto;
        }}

        @media (max-width: 1024px) {{
            .heatmap-calendar {{
                grid-template-columns: auto repeat(7, 1fr);
            }}
        }}

        @media (max-width: 768px) {{
            .heatmap-calendar {{
                grid-template-columns: auto repeat(5, 1fr);
                gap: 3px;
                font-size: 12px;
            }}

            .heatmap-day-label {{
                font-size: 10px;
                padding: 6px 8px;
            }}

            .heatmap-date {{
                font-size: 9px;
            }}

            .heatmap-cell {{
                font-size: 9px;
            }}
        }}

        @media (max-width: 480px) {{
            .heatmap-calendar {{
                grid-template-columns: auto repeat(3, 1fr);
                gap: 2px;
            }}

            .heatmap-day-label {{
                font-size: 9px;
                padding: 4px 6px;
            }}

            .heatmap-date {{
                font-size: 8px;
            }}

            .heatmap-cell {{
                font-size: 8px;
            }}
        }}

        .heatmap-day-label {{
            font-size: 11px;
            color: var(--text-secondary);
            padding: 8px 12px;
            text-align: right;
        }}

        .heatmap-date {{
            font-size: 10px;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 4px;
        }}

        .heatmap-cell {{
            aspect-ratio: 1;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .heatmap-cell:hover {{
            transform: scale(1.1);
        }}

        .heatmap-cell.intensity-0 {{
            background: #20c997;
            color: white;
        }}

        .heatmap-cell.intensity-1 {{
            background: #28a745;
            color: white;
        }}

        .heatmap-cell.intensity-2 {{
            background: #ffc107;
            color: white;
        }}

        .heatmap-cell.intensity-3 {{
            background: #fd7e14;
            color: white;
        }}

        .heatmap-cell.intensity-4 {{
            background: #dc3545;
            color: white;
        }}

        .header h1 {{
            color: var(--text-primary);
            font-size: 28px;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 5px;
        }}

        .header .timestamp {{
            color: var(--brand-primary);
            font-size: 12px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }}

        .category-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 16px;
            flex-direction: row;
        }}

        .category-grid .card {{
            flex: 1;
            min-width: 180px;
        }}

        /* Explicit desktop rules for category grid */
        @media (min-width: 769px) {{
            .category-grid {{
                flex-direction: row !important;
            }}
        }}

        .performance-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 30px;
        }}

        .card {{
            background: var(--bg-secondary);
            padding: 20px 24px;
            border-radius: 4px;
            box-shadow: 0 1px 3px var(--shadow-light);
            border: 1px solid var(--border-color);
            max-width: 100%;
            overflow: hidden;
            transition: box-shadow 0.2s, background-color 0.3s ease;
        }}

        .card:hover {{
            box-shadow: 0 2px 6px var(--shadow-medium);
        }}

        .card h2 {{
            color: var(--text-primary);
            font-size: 16px;
            margin-bottom: 18px;
            font-weight: 600;
            border-bottom: 2px solid var(--brand-primary);
            padding-bottom: 8px;
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
        }}

        .metric:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            font-size: 13px;
            color: var(--text-secondary);
        }}

        .metric-value {{
            font-size: 22px;
            font-weight: 600;
            color: var(--brand-primary);
        }}

        .metric-value.positive {{
            color: #28a745;
        }}

        .metric-value.negative {{
            color: var(--danger-color);
        }}

        .metric-value.warning {{
            color: #ffc107;
        }}

        .progress-bar {{
            width: 100%;
            height: 24px;
            background: var(--chart-bg);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}

        .progress-fill {{
            height: 100%;
            background: var(--brand-primary);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}

        .progress-fill.over-capacity {{
            background: var(--danger-color);
        }}

        .alert {{
            background: rgba(255, 193, 7, 0.1);
            border-left: 4px solid var(--warning-color);
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-size: 13px;
            border: 1px solid var(--warning-color);
            color: var(--text-primary);
        }}

        .alert.danger {{
            background: var(--bg-secondary);
            border-left-color: var(--danger-color);
            border-color: var(--danger-color);
            color: var(--danger-color);
            border-left-width: 4px;
            border-left-style: solid;
        }}

        .alert.success {{
            background: var(--bg-secondary);
            border-left-color: var(--success-color);
            border-color: var(--success-color);
            color: var(--success-color);
            border-left-width: 4px;
            border-left-style: solid;
        }}

        .chart-container {{
            position: relative;
            height: 280px;
            margin-top: 12px;
            max-width: 100%;
            overflow: hidden;
        }}

        .team-member {{
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--card-border, #e9ecef);
            background: var(--bg-secondary);
        }}

        .team-member.capacity-over {{
            border-left: 3px solid var(--danger-color);
        }}

        .team-member.capacity-high {{
            border-left: 3px solid var(--warning-color);
        }}

        .team-member.capacity-ok {{
            border-left: 3px solid #28a745;
        }}

        .team-member-name {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .capacity-status {{
            font-size: 12px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .capacity-status.capacity-over {{
            color: var(--danger-color);
            background: rgba(220, 53, 69, 0.1);
        }}

        .capacity-status.capacity-high {{
            color: #e67e22;
            background: rgba(230, 126, 34, 0.1);
        }}

        .capacity-status.capacity-ok {{
            color: #28a745;
            background: rgba(40, 167, 69, 0.1);
        }}

        .team-member-capacity {{
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        /* Forecast grid default styles */
        .forecast-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 15px;
        }}

        /* Heatmap grid default styles */
        .heatmap-grid {{
            margin-top: 12px;
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 4px;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .card {{
                box-shadow: none;
                border: 1px solid #dee2e6;
                page-break-inside: avoid;
            }}
        }}

        /* Mobile Navigation */
        @media (max-width: 768px) {{
            .nav-container {{
                gap: 15px;
            }}

            .nav-link {{
                font-size: 12px;
                padding: 6px 12px;
            }}
        }}

        @media (max-width: 480px) {{
            .nav-container {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                padding: 0 12px;
            }}

            .nav-link {{
                font-size: 11px;
                padding: 6px 4px;
                text-align: center;
                min-width: 0;
            }}
        }}

        /* Header Mobile Styles */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                align-items: center;
                text-align: center;
            }}

            .header-text {{
                margin-bottom: 15px;
            }}

            .theme-toggle {{
                align-self: flex-end;
            }}
        }}

        @media (max-width: 480px) {{
            .theme-toggle {{
                align-self: center;
            }}
        }}

        /* Mobile Responsive Styles */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
                width: 100%;
                max-width: 100vw;
            }}

            .dashboard-container {{
                width: 100%;
                max-width: 100%;
            }}

            .header {{
                padding: 20px 15px;
            }}

            .header h1 {{
                font-size: 24px;
            }}

            .header .subtitle {{
                font-size: 12px;
            }}

            .grid {{
                grid-template-columns: 1fr !important;
                gap: 15px;
            }}

            .category-grid {{
                flex-direction: column;
                gap: 15px;
            }}

            .category-grid .card {{
                flex: none;
                min-width: auto;
            }}

            .performance-row {{
                grid-template-columns: 1fr !important;
                gap: 15px;
            }}

            /* Override any inline grid styles */
            .card [style*="grid-template-columns"],
            [style*="grid-template-columns"] {{
                grid-template-columns: 1fr !important;
            }}

            .card {{
                padding: 15px;
                width: 100%;
                max-width: 100%;
                box-sizing: border-box;
            }}

            /* Ensure all child elements respect container width */
            .card > * {{
                max-width: 100%;
                box-sizing: border-box;
            }}

            /* Prevent tables and images from overflowing */
            table {{
                width: 100% !important;
                display: block;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                /* Add scrollbar hint */
                box-shadow: inset 0 -1px 0 var(--border-color);
            }}

            /* Mobile table wrapper for better scrolling */
            .card table {{
                min-width: 300px;
            }}

            /* Make table headers sticky on mobile for better UX */
            @supports (position: sticky) {{
                table thead {{
                    position: sticky;
                    top: 0;
                    background: var(--bg-secondary);
                    z-index: 10;
                }}
            }}

            img {{
                max-width: 100%;
                height: auto;
            }}

            /* Fix 6-Month Capacity Timeline bars */
            [style*="min-width: 8px"] {{
                min-width: 3px !important;
            }}

            .card h2 {{
                font-size: 16px;
                margin-bottom: 12px;
            }}

            .metric {{
                padding: 10px 0;
            }}

            .metric-label {{
                font-size: 13px;
            }}

            .metric-value {{
                font-size: 20px;
            }}

            .chart-container {{
                height: 250px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .chart-container canvas {{
                max-width: 100% !important;
                height: auto !important;
            }}

            .velocity-container {{
                height: 250px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .velocity-container canvas {{
                max-width: 100% !important;
                height: auto !important;
            }}

            .team-member-name {{
                font-size: 13px;
            }}

            .alert {{
                padding: 12px;
                font-size: 13px;
            }}

            /* Fix forecast grid - single column on mobile */
            .forecast-grid {{
                grid-template-columns: 1fr !important;
                gap: 15px !important;
            }}

            /* Fix heatmap - fewer columns on mobile */
            .heatmap-grid {{
                grid-template-columns: repeat(5, 1fr) !important;
                gap: 3px !important;
                font-size: 10px !important;
            }}

            .heatmap-grid > div {{
                padding: 6px 4px !important;
                font-size: 10px !important;
            }}
        }}

        /* Extra small mobile devices (iPhone SE, etc.) */
        @media (max-width: 375px) {{
            body {{
                padding: 5px;
            }}

            .header h1 {{
                font-size: 20px;
            }}

            .card {{
                padding: 12px;
            }}

            /* Further reduce timeline bar width on very small screens */
            [style*="min-width: 8px"] {{
                min-width: 2px !important;
            }}

            .card h2 {{
                font-size: 15px;
            }}

            .metric-value {{
                font-size: 18px;
            }}

            .chart-container {{
                height: 220px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .chart-container canvas {{
                max-width: 100% !important;
            }}

            .velocity-container {{
                height: 220px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .velocity-container canvas {{
                max-width: 100% !important;
            }}

            /* Even more compact heatmap for small screens */
            .heatmap-grid {{
                grid-template-columns: repeat(4, 1fr) !important;
                gap: 2px !important;
            }}

            .heatmap-grid > div {{
                padding: 5px 2px !important;
                font-size: 9px !important;
            }}
        }}

        /* Landscape mobile optimization */
        @media (max-width: 768px) and (orientation: landscape) {{
            .chart-container {{
                height: 200px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .chart-container canvas {{
                max-width: 100% !important;
            }}

            .velocity-container {{
                height: 200px;
                width: 100% !important;
                max-width: 100% !important;
            }}

            .velocity-container canvas {{
                max-width: 100% !important;
            }}
        }}

        /* Tablet and Desktop - Restore two-column layout */
        @media (min-width: 769px) {{
            .performance-row {{
                grid-template-columns: 1fr 1fr !important;
                gap: 16px;
            }}
        }}

        /* Large Screen Optimizations */
        @media (min-width: 1920px) {{
            body {{
                font-size: 18px;
                padding: 30px;
            }}

            .header h1 {{
                font-size: 48px;
            }}

            .header .subtitle {{
                font-size: 20px;
            }}

            .header .timestamp {{
                font-size: 16px;
            }}

            .grid {{
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 25px;
            }}

            .category-grid {{
                gap: 25px;
            }}

            .category-grid .card {{
                flex: 1;
                min-width: 200px;
            }}

            .card h2 {{
                font-size: 24px;
            }}

            .metric-label {{
                font-size: 16px;
            }}

            .metric-value {{
                font-size: 36px;
            }}

            .chart-container {{
                height: 400px;
            }}

            .velocity-container {{
                height: 400px;
            }}
        }}

        @media (min-width: 2560px) {{
            body {{
                font-size: 20px;
                padding: 40px;
            }}

            .header h1 {{
                font-size: 56px;
            }}

            .header .subtitle {{
                font-size: 24px;
            }}

            .header .timestamp {{
                font-size: 18px;
            }}

            .grid {{
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
            }}

            .category-grid {{
                gap: 30px;
            }}

            .category-grid .card {{
                flex: 1;
                min-width: 190px;
            }}

            .card {{
                padding: 35px;
            }}

            .card h2 {{
                font-size: 28px;
            }}

            .metric-label {{
                font-size: 18px;
            }}

            .metric-value {{
                font-size: 42px;
            }}

            .chart-container {{
                height: 500px;
            }}

            .velocity-container {{
                height: 500px;
            }}

            .progress-ring {{
                transform: scale(1.25);
            }}


            .progress-ring-value {{
                font-size: 36px;
            }}

            .progress-ring-label {{
                font-size: 14px;
            }}

            .progress-rings-container {{
                gap: 50px !important;
            }}
        }}

        @media (min-width: 3840px) {{
            body {{
                font-size: 24px;
                padding: 50px;
            }}

            .header h1 {{
                font-size: 72px;
            }}

            .header .subtitle {{
                font-size: 32px;
            }}

            .header .timestamp {{
                font-size: 22px;
            }}

            .grid {{
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 40px;
            }}

            .category-grid {{
                gap: 40px;
            }}

            .category-grid .card {{
                flex: 1;
                min-width: 200px;
            }}

            .card {{
                padding: 45px;
                border-radius: 20px;
            }}

            .card h2 {{
                font-size: 36px;
                margin-bottom: 25px;
            }}

            .metric-label {{
                font-size: 22px;
            }}

            .metric-value {{
                font-size: 52px;
            }}

            .chart-container {{
                height: 600px;
            }}

            .velocity-container {{
                height: 600px;
            }}

            .progress-ring {{
                transform: scale(1.5);
            }}


            .progress-ring-value {{
                font-size: 44px;
            }}

            .progress-ring-label {{
                font-size: 16px;
            }}

            .progress-rings-container {{
                gap: 70px !important;
                padding: 40px !important;
            }}

            .team-member-name {{
                font-size: 20px;
            }}

            .team-member-capacity {{
                font-size: 16px;
            }}

            .progress-bar {{
                height: 35px;
            }}

            .progress-fill {{
                font-size: 18px;
                line-height: 35px;
            }}
        }}

    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header" role="banner">
            <div class="header-content">
                <div class="header-text">
                    <h1 id="dashboard-title">Perimeter Studio Dashboard</h1>
                    <p class="subtitle">Video Production Capacity Tracking & Performance Metrics</p>
                    <p class="timestamp" aria-live="polite" aria-label="Dashboard last updated">Last Updated: {data['timestamp']}</p>
                </div>
                <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle dark/light mode" aria-describedby="theme-description">
                    <span id="themeText">Dark Mode</span>
                </button>
            </div>
            <span id="theme-description" class="sr-only">Switch between dark and light themes for better visibility</span>
        </header>

        <!-- Sticky Navigation -->
        <nav class="sticky-nav" role="navigation" aria-label="Dashboard sections">
            <div class="nav-container">
                <a href="#overview" class="nav-link">Overview</a>
                <a href="#capacity" class="nav-link">Team Capacity</a>
                <a href="#metrics" class="nav-link">Key Metrics</a>
                <a href="#deadlines" class="nav-link">Deadlines</a>
                <a href="#forecasts" class="nav-link">Forecasts</a>
                <a href="#analytics" class="nav-link">Analytics</a>
            </div>
        </nav>

        <main role="main" aria-labelledby="dashboard-title">
            <!-- Two-column layout for Performance Overview and Contracted/Outsourced Projects -->
            <div id="overview" class="performance-row" role="region" aria-label="Performance metrics and charts">
            <!-- Performance Overview -->
            <section class="card" role="region" aria-labelledby="performance-title">
                <h2 id="performance-title">Performance Overview</h2>
                <div class="metric" role="group" aria-labelledby="active-tasks-label">
                    <span id="active-tasks-label" class="metric-label">Active Tasks</span>
                    <span class="metric-value" aria-describedby="active-tasks-label">{total_tasks}</span>
                </div>
                <div class="metric" role="group" aria-labelledby="completed-30d-label">
                    <span id="completed-30d-label" class="metric-label">Projects Completed (30d)</span>
                    <span class="metric-value" aria-describedby="completed-30d-label">{delivery_metrics['total_completed']}</span>
                </div>
                <div class="metric" role="group" aria-labelledby="completed-year-label">
                    <span id="completed-year-label" class="metric-label">Projects Completed This Year</span>
                    <span class="metric-value" aria-describedby="completed-year-label">{delivery_metrics['completed_this_year']}</span>
                </div>
                <div class="metric" role="group" aria-labelledby="avg-variance-label">
                    <span id="avg-variance-label" class="metric-label">Avg Days Variance</span>
                    <span class="metric-value {'positive' if delivery_metrics['avg_days_variance'] <= 0 else 'warning' if delivery_metrics['avg_days_variance'] <= 3 else 'negative'}" aria-describedby="avg-variance-label" role="status" aria-label="Average project variance in days">{delivery_metrics['avg_days_variance']:+.1f}</span>
                </div>
                <div class="metric" role="group" aria-labelledby="delayed-capacity-label">
                    <span id="delayed-capacity-label" class="metric-label">Delayed Due to Capacity</span>
                    <span class="metric-value {'positive' if delivery_metrics['projects_delayed_capacity'] == 0 else 'negative'}" aria-describedby="delayed-capacity-label" role="status">{delivery_metrics['projects_delayed_capacity']}</span>
                </div>
            </section>

            <!-- Contracted/Outsourced Projects -->
            <div class="card">
                <h2>Contracted/Outsourced Projects</h2>
"""

    # Add external projects in the new structure
    external_projects = data.get('external_projects', [])
    if external_projects:
        for project in external_projects:
            html += f"""
                <div class="metric">
                    <span class="metric-label">{project['name']}</span>
                    <span class="metric-value">{project['active_count']} Active</span>
                </div>
"""
            if project.get('tasks'):
                html += """
                <div class="external-project-item">
"""
                for task in project['tasks']:
                    due_text = f" (Due: {task['due_on']})" if task.get('due_on') else ""
                    videographer_text = f" | Videographer: {task['videographer']}" if task.get('videographer') else ""
                    html += f"""
                    <div class="task-list-item">• {task['name']}{videographer_text}{due_text}</div>
"""
                html += """
                </div>
"""
    else:
        html += """
            <div class="empty-state">
                <div style="font-size: 16px; color: var(--text-secondary);">No external projects</div>
            </div>
"""

    html += """
            </div>
        </div>

        <!-- Team Capacity (Full Width) -->
        <div id="capacity" class="grid">
            <section class="card full-width" role="region" aria-labelledby="team-capacity-title">
                <h2 id="team-capacity-title">Team Capacity</h2>
                <div class="team-capacity-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 10px;" role="list" aria-label="Team member capacity overview">
"""

    # Add team members
    for member in team_capacity:
        utilization = (member['current'] / member['max'] * 100) if member['max'] > 0 else 0
        over_capacity = member['current'] > member['max']

        # Determine status label and CSS class
        if over_capacity:
            status_label = f"Over capacity (+{member['current'] - member['max']:.0f}%)"
            status_class = "capacity-over"
        elif utilization >= 80:
            status_label = "Near capacity"
            status_class = "capacity-high"
        else:
            status_label = "Available"
            status_class = "capacity-ok"

        tooltip_text = f"Allocated: {member['current']:.1f}% of {member['max']}% max"

        # Bar fill: show allocation relative to max (capped at 100% width)
        bar_pct = min(utilization, 100)

        html += f"""
                    <div class="team-member tooltip {status_class}" role="listitem" tabindex="0" aria-labelledby="member-{member['name'].replace(' ', '-').lower()}-name" data-tooltip="{tooltip_text}">
                        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                            <div id="member-{member['name'].replace(' ', '-').lower()}-name" class="team-member-name">{member['name']}</div>
                            <div class="capacity-status {status_class}">{status_label}</div>
                        </div>
                        <div class="team-member-capacity" aria-label="Current capacity utilization">{member['current']:.0f}% / {member['max']}% capacity</div>
                        <div class="progress-bar" role="progressbar" aria-valuenow="{utilization:.0f}" aria-valuemin="0" aria-valuemax="100" aria-label="Capacity utilization: {utilization:.0f}%">
                            <div class="progress-fill {'over-capacity' if over_capacity else ''}" style="width: {bar_pct}%" aria-hidden="true">
                                {member['current']:.0f}% allocated
                            </div>
                        </div>
                    </div>
"""

    html += """
                </div>
        </section>

        <!-- At-Risk Tasks (Full Width) -->
        <div class="card full-width" style="margin-top: 30px; margin-bottom: 30px;">
            <h2>At-Risk Tasks</h2>
    """

    at_risk = data.get('at_risk_tasks', [])
    if at_risk:
        html += """
            <div style="margin-top: 15px;">
        """
        for task in at_risk[:10]:  # Show top 10
            risks_html = "<br>".join([f"• {risk}" for risk in task['risks']])
            videographer_display = f" | Videographer: {task.get('videographer', 'N/A')}" if task.get('videographer') else ""
            html += f"""
                <div class="at-risk-item">
                    <div class="project-task-name">{task['name']}</div>
                    <div class="task-detail">
                        {task['project']} | {task['assignee']}{videographer_display} | Due: {task['due_on']}
                    </div>
                    <div class="task-risk">
                        {risks_html}
                    </div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += """
            <div class="success-state">
                <div style="font-size: 18px;">No tasks currently at risk</div>
            </div>
        """

    html += """
        </div>

        <!-- Upcoming Shoots -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Upcoming Shoots</h2>
    """

    upcoming_shoots = data.get('upcoming_shoots', [])
    if upcoming_shoots:
        html += """
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 18px;">
        """
        for shoot in upcoming_shoots:
            # Format date and time
            shoot_datetime = shoot['datetime']
            from datetime import timezone

            # Check if this is a date-only field (midnight UTC)
            is_date_only = (shoot_datetime.hour == 0 and shoot_datetime.minute == 0 and
                           shoot_datetime.second == 0 and shoot_datetime.tzinfo == timezone.utc)

            if is_date_only:
                # For date-only fields, don't convert to local time - use the date as-is
                date_str = shoot_datetime.strftime('%a, %b %-d')
                time_str = shoot_datetime.strftime('%-I:%M %p')
            else:
                # Convert from UTC to local time for datetime fields
                local_datetime = shoot_datetime.astimezone()
                # Format date as "Mon, Dec 4"
                date_str = local_datetime.strftime('%a, %b %-d')
                # Format time as "3:45 PM"
                time_str = local_datetime.strftime('%-I:%M %p')

            # Generate Asana task URL
            task_url = f"https://app.asana.com/0/0/{shoot['gid']}/f"

            html += f"""
                <div class="project-card">
                    <div class="project-card-header">
                        <div>
                            <div class="project-card-date">{date_str}</div>
                            <div class="project-card-time">{time_str}</div>
                        </div>
                        <span class="project-card-badge">{shoot['project']}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" class="project-card-title">
                            {shoot['name']}
                        </a>
                    </div>
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 2px solid #dee2e6;">
                        <a href="{task_url}" target="_blank" style="color: {BRAND_BLUE}; text-decoration: none; font-size: 14px;">
                            View in Asana →
                        </a>
                    </div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += """
            <div style="text-align: center; padding: 30px; color: var(--text-secondary);">
                <div style="font-size: 16px;">No upcoming shoots scheduled</div>
            </div>
        """

    html += """
        </div>

        <!-- Upcoming Project Deadlines -->
        <div id="deadlines" class="card full-width" style="margin-bottom: 30px;">
            <h2>Upcoming Project Deadlines</h2>
            <p style="color: var(--text-secondary); margin-top: 8px; font-size: 14px;">Projects due within the next 10 days</p>
    """

    upcoming_deadlines = data.get('upcoming_deadlines', [])
    if upcoming_deadlines:
        html += """
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 18px;">
        """
        for deadline in upcoming_deadlines:
            # Format date
            due_date = deadline['due_date']
            date_str = due_date.strftime('%a, %b %-d, %Y')

            # Generate Asana task URL
            task_url = f"https://app.asana.com/0/0/{deadline['gid']}/f"

            # Determine urgency color
            days_until = deadline['days_until']
            if days_until == 0:
                urgency_color = '#dc3545'  # Red for today
                urgency_text = 'DUE TODAY'
            elif days_until == 1:
                urgency_color = '#fd7e14'  # Orange for tomorrow
                urgency_text = 'DUE TOMORROW'
            elif days_until <= 3:
                urgency_color = '#ffc107'  # Yellow for within 3 days
                urgency_text = f'{days_until} DAYS'
            else:
                urgency_color = BRAND_BLUE
                urgency_text = f'{days_until} DAYS'

            html += f"""
                <div class="project-card">
                    <div class="project-card-header">
                        <div>
                            <div class="project-card-date">{date_str}</div>
                            <div style="font-size: 22px; font-weight: 600; color: {urgency_color}; margin-top: 6px;">{urgency_text}</div>
                        </div>
                        <span class="project-card-badge">{deadline['project']}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" class="project-card-title">
                            {deadline['name']}
                        </a>
                    </div>
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 2px solid #dee2e6;">
                        <a href="{task_url}" target="_blank" style="color: {BRAND_BLUE}; text-decoration: none; font-size: 14px;">
                            View in Asana →
                        </a>
                    </div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += f"""
            <div style="text-align: center; padding: 30px; color: var(--text-secondary);">
                <div style="font-size: 16px;">No upcoming deadlines in the next 10 days</div>
            </div>
        """

    html += """
        </div>

        <!-- Progress Rings -->
        <div id="metrics" class="card full-width" style="margin-bottom: 30px; overflow: visible !important; padding: 40px 50px;">
            <h2>Key Performance Metrics</h2>
            <div class="progress-rings-container" style="overflow: visible !important;">
                <div class="progress-ring">
                    <svg class="progress-ring-svg" width="140" height="140">
                        <circle class="progress-ring-circle progress-ring-bg" cx="70" cy="70" r="55"></circle>
                        <circle class="progress-ring-circle progress-ring-progress" cx="70" cy="70" r="55"
                                stroke="var(--success-color)" id="ringOnTime"></circle>
                    </svg>
                    <div class="progress-ring-text">
                        <span class="progress-ring-value" id="ringOnTimeValue">0%</span>
                        <span class="progress-ring-label">On-Time Delivery</span>
                    </div>
                </div>
                <div class="progress-ring">
                    <svg class="progress-ring-svg" width="140" height="140">
                        <circle class="progress-ring-circle progress-ring-bg" cx="70" cy="70" r="55"></circle>
                        <circle class="progress-ring-circle progress-ring-progress" cx="70" cy="70" r="55"
                                stroke="var(--brand-primary)" id="ringUtilization"></circle>
                    </svg>
                    <div class="progress-ring-text">
                        <span class="progress-ring-value" id="ringUtilizationValue">0%</span>
                        <span class="progress-ring-label">Team Utilization</span>
                    </div>
                </div>
                <div class="progress-ring">
                    <svg class="progress-ring-svg" width="140" height="140">
                        <circle class="progress-ring-circle progress-ring-bg" cx="70" cy="70" r="55"></circle>
                        <circle class="progress-ring-circle progress-ring-progress" cx="70" cy="70" r="55"
                                stroke="var(--info-color)" id="ringProjects"></circle>
                    </svg>
                    <div class="progress-ring-text">
                        <span class="progress-ring-value" id="ringProjectsValue">0</span>
                        <span class="progress-ring-label">Active Projects</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Timeline Gantt -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Project Timeline</h2>
            <p style="color: var(--text-secondary); margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Next 10 days</p>
            <div class="timeline-container" id="projectTimeline">
                <!-- Timeline will be generated by JavaScript -->
            </div>
        </div>


        <!-- Velocity Trend Chart -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Team Velocity Trend</h2>
            <p style="color: var(--text-secondary); margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Projects completed per week over the last 8 weeks</p>
            <div class="velocity-container">
                <canvas id="velocityChart"></canvas>
            </div>
        </div>

        <!-- 6-Month Capacity Timeline -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>6-Month Capacity Timeline</h2>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 15px;">
                Weekly team capacity projection showing workload distribution over the next 26 weeks
            </div>
    """

    # Add 6-month timeline data
    timeline = data.get('six_month_timeline', [])

    html += """
            <div style="margin-top: 15px;">
                <!-- Timeline header with month labels -->
                <div style="display: flex; margin-bottom: 10px; font-size: 12px; font-weight: bold; color: var(--text-secondary);">
    """

    # Group weeks by month for header labels
    current_month = None
    month_week_count = 0
    for week in timeline:
        if week['month'] != current_month:
            if current_month is not None:
                # Close previous month label
                html += f"""
                    <div style="flex: {month_week_count}; text-align: center; border-right: 1px solid #dee2e6;">{current_month}</div>
                """
            current_month = week['month']
            month_week_count = 1
        else:
            month_week_count += 1

    # Close last month label
    if current_month:
        html += f"""
                    <div style="flex: {month_week_count}; text-align: center;">{current_month}</div>
        """

    html += """
                </div>

                <!-- Timeline bars -->
                <div style="display: flex; gap: 3px; height: 60px; align-items: flex-end;">
    """

    # Add timeline bars
    for week in timeline:
        utilization = week.get('utilization', 0)
        status = week.get('status', 'good')
        task_count = week.get('task_count', 0)
        week_num = week.get('week_num', 0)
        start_date = week.get('start_date', '')

        # Color based on status (adaptive scaling like heatmap)
        if status == 'over':
            bar_color = '#dc3545'  # Red (very high)
        elif status == 'warning':
            bar_color = '#fd7e14'  # Orange (high)
        elif status == 'busy':
            bar_color = '#ffc107'  # Yellow (medium)
        else:
            bar_color = '#28a745'  # Green (low)

        # Calculate visual bar height with scaling for better visibility
        # Apply 1.3x multiplier with 5% minimum for maximum variance while keeping bars clickable
        # This doesn't change the data, just makes differences much more apparent
        bar_height = max(5, min(utilization * 1.3, 100))

        html += f"""
                    <div style="flex: 1; background: {bar_color}; height: {bar_height}%; border-radius: 4px 4px 0 0; position: relative; min-width: 8px; cursor: pointer;"
                         title="Week {week_num} ({start_date}): {utilization:.0f}% capacity, {task_count} tasks">
                    </div>
        """

    html += """
                </div>

                <!-- Week number labels (show every 4th week) -->
                <div style="display: flex; gap: 3px; margin-top: 5px; font-size: 9px; color: var(--text-secondary);">
    """

    for i, week in enumerate(timeline):
        week_num = week.get('week_num', 0)
        # Show label every 4 weeks
        if i % 4 == 0:
            html += f"""
                    <div style="flex: 1; text-align: center; min-width: 8px;">W{week_num}</div>
            """
        else:
            html += """
                    <div style="flex: 1; min-width: 8px;"></div>
            """

    html += """
                </div>

                <!-- Legend -->
                <div style="margin-top: 15px; font-size: 11px; color: var(--text-secondary); display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 2px;"></span> Low</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; border-radius: 2px;"></span> Medium</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #fd7e14; border-radius: 2px;"></span> High</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; border-radius: 2px;"></span> Very High</div>
                </div>
                <div style="margin-top: 5px; font-size: 10px; color: var(--text-secondary); text-align: center; font-style: italic;">
                    Colors scale adaptively based on peak workload over the 6-month period
                </div>
            </div>
        </div>

        <!-- Daily Workload Distribution Heatmap -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Daily Workload Distribution - Next 30 Days</h2>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 15px;">
                <strong>How busy will each day be?</strong> Shows the team's expected workload intensity per day (work distributed across task timelines)
            </div>
            <div class="heatmap-grid">
    """

    heatmap = data.get('capacity_heatmap', [])
    for day_data in heatmap:
        date_str = day_data.get('date', '')  # Full date like "2025-11-26"
        day_abbr = day_data.get('day', '')  # Day abbreviation like "Wed"
        utilization = day_data.get('utilization', 0)
        status = day_data.get('status', 'low')

        # Format date for display (show month/day)
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            display_date = date_obj.strftime('%m/%d')  # Shows as "11/26"
        except:
            display_date = day_abbr

        # Color based on utilization with 5-color gradient
        if status == 'very_high':
            bg_color = '#dc3545'  # Red
        elif status == 'high':
            bg_color = '#fd7e14'  # Orange
        elif status == 'medium':
            bg_color = '#ffc107'  # Yellow
        elif status == 'low':
            bg_color = '#28a745'  # Green
        else:  # very_low
            bg_color = '#20c997'  # Light teal-green

        html += f"""
                <div style="background: {bg_color}; color: white; padding: 8px; border-radius: 4px; text-align: center; font-size: 11px;" title="{date_str}: {utilization:.1f}% capacity">
                    <div style="font-weight: bold;">{display_date}</div>
                    <div style="font-size: 9px; margin-top: 2px;">{utilization:.0f}%</div>
                </div>
        """

    html += f"""
            </div>
            <div style="margin-top: 15px; font-size: 11px; color: var(--text-secondary); display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #20c997; border-radius: 2px;"></span> Very Low</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 2px;"></span> Low</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; border-radius: 2px;"></span> Medium</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #fd7e14; border-radius: 2px;"></span> High</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; border-radius: 2px;"></span> Very High</div>
            </div>
            <div style="margin-top: 10px; font-size: 11px; color: var(--text-secondary); text-align: center;">
                <em>Colors scale adaptively based on peak workload over the 30-day period</em>
            </div>
        </div>

        <!-- Historical Capacity Utilization -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Historical Capacity Utilization</h2>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
                Team utilization percentage over the last 30 days (click legend items to filter)
            </div>
            <div class="chart-container">
                <canvas id="capacityHistoryChart"></canvas>
            </div>
        </div>

        <!-- Forecasted Projects -->
        <div id="forecasts" class="card full-width" style="margin-bottom: 30px;">
            <h2>Forecasted Projects</h2>
            <p style="color: var(--text-secondary); margin-top: 8px; font-size: 14px;">Upcoming projects in the forecast pipeline</p>
    """

    forecasted_projects = data.get('forecasted_projects', [])
    if forecasted_projects:
        html += """
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 18px;">
        """
        for project in forecasted_projects:
            # Format dates
            date_range_str = ""
            if project['start_on'] and project['due_date']:
                start_str = project['start_on'].strftime('%b %-d')
                due_str = project['due_date'].strftime('%b %-d, %Y')
                date_range_str = f"{start_str} - {due_str}"
            elif project['due_date']:
                date_range_str = project['due_date'].strftime('%b %-d, %Y')
            elif project['start_on']:
                date_range_str = f"Starts {project['start_on'].strftime('%b %-d, %Y')}"
            else:
                date_range_str = "Date TBD"

            # Generate Asana task URL
            task_url = f"https://app.asana.com/0/0/{project['gid']}/f"

            # Truncate notes if too long
            notes = project.get('notes', '')
            if len(notes) > 150:
                notes = notes[:150] + '...'

            html += f"""
                <div class="project-card">
                    <div class="project-card-header">
                        <div style="flex: 1;">
                            <div class="project-card-date">{date_range_str}</div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" class="project-card-title" style="font-weight: 600;">
                            {project['name']}
                        </a>
                    </div>
            """

            if notes:
                html += f"""
                    <div style="margin-bottom: 12px; color: var(--text-secondary); font-size: 14px; line-height: 1.5;">
                        {notes}
                    </div>
                """

            html += f"""
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 2px solid #dee2e6;">
                        <a href="{task_url}" target="_blank" style="color: {BRAND_BLUE}; text-decoration: none; font-size: 14px;">
                            View in Asana →
                        </a>
                    </div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += f"""
            <div style="text-align: center; padding: 30px; color: var(--text-secondary);">
                <div style="font-size: 16px;">No forecasted projects at this time</div>
            </div>
        """

    html += """
        </div>

        <!-- Radar/Spider Chart -->
        <div class="card full-width" style="margin-bottom: 30px; overflow: visible;">
            <h2>Workload Balance</h2>
            <p style="color: var(--text-secondary); margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Actual vs Target distribution across categories</p>
            <div class="radar-container" id="radarChart">
                <!-- Radar will be generated by JavaScript -->
            </div>
        </div>

        <!-- Historical Trends Chart -->
        <div id="analytics" class="card full-width" style="margin-bottom: 30px;">
            <h2>Historical Allocation Trends</h2>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
                Daily allocation percentages over time
            </div>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
            </div>
        </div>

        <!-- Category Performance Summary -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Category Performance Summary</h2>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 20px;">
                Allocation performance across all project categories
            </div>

            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border-color);">
                            <th style="text-align: left; padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Category</th>
                            <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Cumulative Avg</th>
                            <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Annual Target</th>
                            <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Variance</th>
                            <th style="text-align: center; padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Status</th>
                        </tr>
                    </thead>
                    <tbody>"""

    # Add category rows
    for i, cat in enumerate(category_data):
        variance_class = 'positive' if abs(cat['variance']) <= 5 else 'warning' if abs(cat['variance']) <= 10 else 'negative'

        # Determine status based on variance magnitude and direction
        if abs(cat['variance']) <= 5:
            status_icon = '✓'
            status_text = 'On Track'
        elif abs(cat['variance']) <= 10:
            status_icon = '!'
            status_text = 'Watch'
        else:
            status_icon = '!'
            if cat['variance'] > 0:
                status_text = 'Over Allocated'
            else:
                status_text = 'Under Allocated'

        # Alternate row colors
        row_bg = 'rgba(96, 187, 233, 0.05)' if i % 2 == 0 else 'transparent'

        html += f"""
                        <tr style="background: {row_bg}; border-bottom: 1px solid var(--border-color);">
                            <td style="padding: 12px 16px; font-weight: 500; color: var(--text-primary);">{cat['name']}</td>
                            <td style="padding: 12px 16px; text-align: right; font-weight: 500;">{cat['actual']:.1f}%</td>
                            <td style="padding: 12px 16px; text-align: right; color: var(--text-secondary);">{cat['target']:.1f}%</td>
                            <td style="padding: 12px 16px; text-align: right; font-weight: 600;" class="{variance_class}">{cat['variance']:+.1f}%</td>
                            <td style="padding: 12px 16px; text-align: center; font-size: 12px;">
                                <span style="display: inline-flex; align-items: center; gap: 4px;">
                                    <span>{status_icon}</span>
                                    <span>{status_text}</span>
                                </span>
                            </td>
                        </tr>"""

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
"""

    # Add Chart.js data
    category_names = [cat['name'] for cat in category_data]
    actual_values = [cat['actual'] for cat in category_data]  # Cumulative averages
    target_values = [cat['target'] for cat in category_data]

    # Prepare timeline data for JavaScript
    shoots_data = []
    for s in data.get('upcoming_shoots', []):
        # Remove checkbox characters from name
        clean_name = s['name'].replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()
        shoot_dict = {
            'name': clean_name,
            'datetime': s['datetime'].isoformat(),
            'start_on': s['start_on'].isoformat() if s.get('start_on') else None,
            'due_on': s['due_on'].isoformat() if s.get('due_on') else None,
            'type': 'shoot'
        }
        shoots_data.append(shoot_dict)
    shoots_json = json.dumps(shoots_data)

    deadlines_data = []
    for d in data.get('upcoming_deadlines', []):
        # Remove checkbox characters from name
        clean_name = d['name'].replace('☐', '').replace('☑', '').replace('✓', '').replace('✔', '').strip()
        deadline_dict = {
            'name': clean_name,
            'start_on': d['start_on'].isoformat() if d.get('start_on') else None,
            'due_date': d['due_date'].isoformat(),
            'type': 'deadline'
        }
        deadlines_data.append(deadline_dict)
    deadlines_json = json.dumps(deadlines_data)

    # Prepare radar chart data
    radar_categories_json = json.dumps([{'name': cat['name'], 'actual': cat['actual'], 'target': cat['target']} for cat in category_data])

    # Calculate average team utilization
    team_utilization_avg = sum((member['current'] / member['max'] * 100) if member['max'] > 0 else 0 for member in team_capacity) / len(team_capacity) if team_capacity else 0

    # Calculate weekly velocity from delivery log
    weekly_completions = []
    if data['delivery_log'] is not None and not data['delivery_log'].empty:
        df = data['delivery_log']
        if 'Completed Date' in df.columns:
            # Get completions for the last 8 weeks
            today = datetime.now().date()
            for week_offset in range(7, -1, -1):  # 7 weeks ago to current week
                week_start = today - timedelta(weeks=week_offset, days=today.weekday())
                week_end = week_start + timedelta(days=6)

                # Count completions in this week
                week_count = 0
                for _, task in df.iterrows():
                    if pd.notna(task['Completed Date']):
                        try:
                            completion_date = pd.to_datetime(task['Completed Date']).date()
                            if week_start <= completion_date <= week_end:
                                week_count += 1
                        except (ValueError, TypeError):
                            pass

                weekly_completions.append(week_count)

    # If no data available, create estimated data based on average
    if not weekly_completions or sum(weekly_completions) == 0:
        total_completed = delivery_metrics['total_completed']
        avg_per_week = max(1, total_completed / 4)  # 30 days ≈ 4 weeks, minimum 1
        variance = 0.4  # 40% variation for more interesting chart
        for i in range(8):
            variation = (0.5 - (i % 3) * 0.2)  # Create a pattern instead of random
            weekly_completions.append(max(1, round(avg_per_week * (1 + variation * variance))))

    weekly_completions_json = json.dumps(weekly_completions)

    # Extract current period data (latest day from variance_history)
    current_values = []
    if 'variance_history' in data and data['variance_history'] is not None:
        history_df = data['variance_history']
        if not history_df.empty:
            latest_date = history_df['Date'].max()
            latest_data = history_df[history_df['Date'] == latest_date]
            # Match category order
            for cat_name in category_names:
                cat_row = latest_data[latest_data['Category'] == cat_name]
                if not cat_row.empty:
                    current_values.append(float(cat_row['Actual %'].iloc[0]))
                else:
                    current_values.append(0)
        else:
            current_values = actual_values  # Fallback to cumulative
    else:
        current_values = actual_values  # Fallback to cumulative

    html += f"""
        // Historical Trends Chart
"""

    # Prepare historical trends data
    if 'variance_history' in data and data['variance_history'] is not None:
        history_df = data['variance_history']
        # Get unique dates and categories
        dates = sorted(history_df['Date'].unique().tolist())
        categories = history_df['Category'].unique().tolist()

        # Create datasets for each category
        trends_datasets = []
        colors = ['#28a745', '#9B59B6', '#2196F3', '#ffc107', '#dc3545']  # Green, Purple, Blue, Yellow, Red

        for i, category in enumerate(categories):
            cat_data = history_df[history_df['Category'] == category]
            values = []
            for date in dates:
                row = cat_data[cat_data['Date'] == date]
                if not row.empty:
                    values.append(float(row['Actual %'].iloc[0]))
                else:
                    values.append(None)

            color = colors[i % len(colors)]
            trends_datasets.append({
                'label': category,
                'data': values,
                'borderColor': color,
                'backgroundColor': color,
                'borderWidth': 2,
                'fill': False,
                'tension': 0.1
            })

        html += f"""
        // Function to get theme-aware colors
        function getChartTextColor() {{
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            return isDarkMode ? '#ffffff' : '#333333';
        }}

        function getChartGridColor() {{
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            return isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        }}

        // Function to get theme-aware dataset colors
        function getThemeAwareMemberColors() {{
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDarkMode) {{
                return {{
                    'Zach Welliver': '#C694FF',   // Lighter purple
                    'Nick Clark': '#5DADE2',      // Lighter blue
                    'Adriel Abella': '#F4D03F',   // Lighter yellow
                    'John Meyer': '#7DCEA0',      // Lighter teal
                    'Team Total': '#60BBE9'       // Brand blue works in both themes
                }};
            }} else {{
                return {{
                    'Zach Welliver': '#9B59B6',   // Original purple
                    'Nick Clark': '#36A2EB',      // Original blue
                    'Adriel Abella': '#FFCE56',   // Original yellow
                    'John Meyer': '#4BC0C0',      // Original teal
                    'Team Total': '#60BBE9'       // Brand blue
                }};
            }}
        }}

        // Function to get theme-aware trend colors
        function getThemeAwareTrendColors() {{
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDarkMode) {{
                return ['#7DCEA0', '#C694FF', '#60BBE9', '#FFD700', '#FF6B6B'];  // Green, Purple, Blue, Gold, Red for dark mode
            }} else {{
                return ['#28a745', '#9B59B6', '#2196F3', '#ffc107', '#dc3545'];  // Green, Purple, Blue, Yellow, Red for light mode
            }}
        }}

        const trendsCtx = document.getElementById('trendsChart').getContext('2d');

        // Update dataset colors for theme
        const trendColors = getThemeAwareTrendColors();
        const trendsDataWithColors = {json.dumps(trends_datasets)};
        trendsDataWithColors.forEach((dataset, index) => {{
            if (index < trendColors.length) {{
                dataset.borderColor = trendColors[index];
                dataset.backgroundColor = trendColors[index];
            }}
        }});

        window.trendsChart = new Chart(trendsCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: trendsDataWithColors
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            color: getChartTextColor(),
                            font: {{
                                size: window.innerWidth < 768 ? 10 : 12
                            }},
                            callback: function(value) {{
                                return value + '%';
                            }},
                            maxTicksLimit: window.innerWidth < 768 ? 6 : 10
                        }},
                        grid: {{
                            color: getChartGridColor(),
                            display: window.innerWidth >= 480
                        }}
                    }},
                    x: {{
                        ticks: {{
                            color: getChartTextColor(),
                            font: {{
                                size: window.innerWidth < 768 ? 9 : 11
                            }},
                            maxRotation: window.innerWidth < 768 ? 90 : 45,
                            minRotation: window.innerWidth < 768 ? 90 : 45,
                            autoSkip: true,
                            autoSkipPadding: window.innerWidth < 768 ? 20 : 10,
                            maxTicksLimit: window.innerWidth < 480 ? 10 : (window.innerWidth < 768 ? 15 : 20)
                        }},
                        grid: {{
                            color: getChartGridColor(),
                            display: false
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: window.innerWidth < 768 ? 'bottom' : 'top',
                        labels: {{
                            color: getChartTextColor(),
                            font: {{
                                size: window.innerWidth < 768 ? 10 : 12
                            }},
                            padding: window.innerWidth < 768 ? 8 : 10,
                            boxWidth: window.innerWidth < 768 ? 12 : 15,
                            boxHeight: window.innerWidth < 768 ? 12 : 15
                        }}
                    }},
                    tooltip: {{
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        titleFont: {{
                            size: window.innerWidth < 768 ? 11 : 13
                        }},
                        bodyFont: {{
                            size: window.innerWidth < 768 ? 10 : 12
                        }},
                        padding: window.innerWidth < 768 ? 8 : 12,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
"""

    # Add Historical Capacity Utilization Chart with per-member data
    capacity_history_by_member = data.get('capacity_history_by_member', {})

    html += f"""
        // Historical Capacity Utilization Chart with per-member datasets
        function generateCapacityHistoryChart() {{
            console.log('=== generateCapacityHistoryChart called ===');

            // Destroy existing chart if it exists
            if (window.capacityHistoryChart) {{
                console.log('Destroying existing chart');
                try {{
                    window.capacityHistoryChart.destroy();
                }} catch (e) {{
                    console.log('Error destroying chart:', e);
                }}
                window.capacityHistoryChart = null;
            }}

            const chartElement = document.getElementById('capacityHistoryChart');
            console.log('Chart element found:', !!chartElement);

            if (chartElement) {{
                // Force refresh container dimensions before creating chart
                chartElement.style.display = 'block';
                chartElement.style.visibility = 'visible';
                chartElement.style.opacity = '1';

                // Trigger reflow to ensure dimensions are calculated
                const width = chartElement.offsetWidth;
                const height = chartElement.offsetHeight;
                console.log('Chart container dimensions:', width, 'x', height);
                console.log('Chart container style:', chartElement.style.cssText);

                // Ensure minimum dimensions for chart visibility
                if (width < 200) {{
                    console.log('Container width too small, setting minimum width');
                    chartElement.style.minWidth = '300px';
                }}
                if (height < 150) {{
                    console.log('Container height too small, setting minimum height');
                    chartElement.style.minHeight = '200px';
                }}

                const historyCtx = chartElement.getContext('2d');
                console.log('Canvas context obtained:', !!historyCtx);

                const capacityHistoryByMember = {json.dumps(capacity_history_by_member)};
                console.log('Data received:', Object.keys(capacityHistoryByMember), 'members with data');

                // Build datasets for each team member
                const datasets = [];
                const memberColors = getThemeAwareMemberColors();

                // Extract all unique dates from Team Total (or first available member)
                let allDates = [];
                if (capacityHistoryByMember['Team Total']) {{
                    allDates = capacityHistoryByMember['Team Total'].map(d => d.date);
                }} else {{
                    // Fallback to first member with data
                    const firstMember = Object.keys(capacityHistoryByMember)[0];
                    if (firstMember) {{
                        allDates = capacityHistoryByMember[firstMember].map(d => d.date);
                    }}
                }}

                console.log('About to build datasets...');
                console.log('All dates found:', allDates.length, 'dates from', allDates[0], 'to', allDates[allDates.length - 1]);

                // Create dataset for each team member
                const memberOrder = ['Zach Welliver', 'Nick Clark', 'Adriel Abella', 'John Meyer', 'Team Total'];
                memberOrder.forEach(memberName => {{
                    if (capacityHistoryByMember[memberName]) {{
                        const memberData = capacityHistoryByMember[memberName];
                        const color = memberColors[memberName] || '#999999';
                        const isTeamTotal = memberName === 'Team Total';

                        datasets.push({{
                            label: memberName,
                            data: memberData.map(d => parseFloat(d.utilization_percent)),
                            borderColor: color,
                            backgroundColor: isTeamTotal ? `${{color}}33` : 'transparent',
                            borderWidth: isTeamTotal ? 3 : 2,
                            fill: isTeamTotal,
                            tension: 0.3,
                            pointRadius: isTeamTotal ? 5 : 3,
                            pointBackgroundColor: color,
                            pointBorderColor: color,
                            pointBorderWidth: 2,
                            hidden: false
                        }});
                    }}
                }});

                // Add 100% capacity redline
                const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
                const thresholdColor = isDarkMode ? '#FF6B6B' : '#dc3545';

                datasets.push({{
                    label: '100% Capacity Threshold',
                    data: Array(allDates.length).fill(100),
                    borderColor: thresholdColor,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }});

                console.log('Generated datasets:', datasets.length, 'datasets for chart');
                datasets.forEach((ds, i) => console.log('Dataset', i + ':', ds.label, 'with', ds.data.length, 'data points'));

                if (datasets.length > 0) {{
                    console.log('Dataset details:', datasets.map(d => ({{name: d.label, dataPoints: d.data.length}})));
                }}

                if (datasets.length > 0) {{
                    console.log('About to create chart with', allDates.length, 'labels and', datasets.length, 'datasets');

                    try {{
                        window.capacityHistoryChart = new Chart(historyCtx, {{
                        type: 'line',
                        data: {{
                            labels: allDates,
                            datasets: datasets
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            resizeDelay: 0,
                            devicePixelRatio: window.devicePixelRatio || 1,
                            layout: {{
                                padding: {{
                                    top: window.innerWidth < 768 ? 10 : 20,
                                    bottom: window.innerWidth < 768 ? 10 : 0
                                }}
                            }},
                            interaction: {{
                                mode: 'index',
                                intersect: false
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    suggestedMax: 100,
                                    ticks: {{
                                        color: getChartTextColor(),
                                        font: {{
                                            size: window.innerWidth < 768 ? 10 : 12
                                        }},
                                        callback: function(value) {{
                                            return value + '%';
                                        }},
                                        maxTicksLimit: window.innerWidth < 768 ? 6 : 10
                                    }},
                                    grid: {{
                                        color: getChartGridColor(),
                                        display: window.innerWidth >= 480
                                    }}
                                }},
                                x: {{
                                    ticks: {{
                                        color: getChartTextColor(),
                                        font: {{
                                            size: window.innerWidth < 768 ? 9 : 11
                                        }},
                                        maxRotation: window.innerWidth < 768 ? 90 : 45,
                                        minRotation: window.innerWidth < 768 ? 90 : 45,
                                        autoSkip: true,
                                        autoSkipPadding: window.innerWidth < 768 ? 20 : 10,
                                        maxTicksLimit: window.innerWidth < 480 ? 8 : (window.innerWidth < 768 ? 12 : 20)
                                    }},
                                    grid: {{
                                        color: getChartGridColor(),
                                        display: false
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    position: window.innerWidth < 768 ? 'bottom' : 'top',
                                    labels: {{
                                        color: getChartTextColor(),
                                        usePointStyle: true,
                                        font: {{
                                            size: window.innerWidth < 768 ? 10 : 12
                                        }},
                                        padding: window.innerWidth < 768 ? 6 : 10,
                                        boxWidth: window.innerWidth < 768 ? 10 : 12,
                                        boxHeight: window.innerWidth < 768 ? 10 : 12
                                    }}
                                }},
                                tooltip: {{
                                    enabled: true,
                                    mode: 'index',
                                    intersect: false,
                                    titleFont: {{
                                        size: window.innerWidth < 768 ? 11 : 13
                                    }},
                                    bodyFont: {{
                                        size: window.innerWidth < 768 ? 10 : 12
                                    }},
                                    padding: window.innerWidth < 768 ? 8 : 12,
                                    callbacks: {{
                                        label: function(context) {{
                                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        }});

                        console.log('Chart created successfully:', !!window.capacityHistoryChart);
                    }} catch (error) {{
                        console.error('Error creating capacity history chart:', error);
                        console.log('Chart data that caused error:', {{
                            labels: allDates.slice(0, 5),
                            datasetCount: datasets.length,
                            firstDataset: datasets[0] ? {{
                                label: datasets[0].label,
                                dataLength: datasets[0].data.length,
                                firstFewData: datasets[0].data.slice(0, 5)
                            }} : null
                        }});
                        return;
                    }}
                    if (window.capacityHistoryChart) {{
                        console.log('Chart status - datasets:', window.capacityHistoryChart.data.datasets.length, 'visible:', window.capacityHistoryChart.canvas.style.display !== 'none');
                    }}

                    // Mobile-specific post-creation validation
                    if (isMobile && window.capacityHistoryChart) {{
                        setTimeout(() => {{
                            console.log('Post-creation mobile validation for capacity chart');
                            const chart = window.capacityHistoryChart;
                            if (chart && (!chart.data || !chart.data.datasets || chart.data.datasets.length === 0)) {{
                                console.log('Mobile chart missing data after creation - forcing update');
                                chart.update('none');
                            }}
                        }}, 200);
                    }}
                }} else {{
                    console.log('No datasets generated for capacity history chart');
                }}
            }}
        }}

        // Simple chart initialization check
        window.addEventListener('load', function() {{
            setTimeout(() => {{
                if (!window.capacityHistoryChart) {{
                    console.log('Chart not found on load, creating...');
                    generateCapacityHistoryChart();
                }}
            }}, 500);
        }});

        // Additional chart validation - check every few seconds to ensure chart stays visible
        function validateCapacityChart() {{
            const chartElement = document.getElementById('capacityHistoryChart');
            if (chartElement && (!window.capacityHistoryChart ||
                !window.capacityHistoryChart.canvas ||
                window.capacityHistoryChart.canvas.style.display === 'none')) {{
                console.log('Historical Capacity chart validation failed - recreating');
                if (window.capacityHistoryChart) {{
                    try {{
                        window.capacityHistoryChart.destroy();
                    }} catch (e) {{
                        console.log('Error destroying during validation:', e);
                    }}
                    window.capacityHistoryChart = null;
                }}
                generateCapacityHistoryChart();
            }}
        }}

        // Run validation after DOM changes or potential CSS recalculations
        setTimeout(() => {{
            validateCapacityChart();
            setInterval(validateCapacityChart, 10000); // Check every 10 seconds
        }}, 2000);

        // ===== NEW CHART VISUALIZATIONS =====

        // Progress Rings
        function animateProgressRing(elementId, valueId, percentage, isNumber = false) {{
            const ring = document.getElementById(elementId);
            const valueEl = document.getElementById(valueId);
            if (!ring || !valueEl) return;

            const radius = 55;
            const circumference = 2 * Math.PI * radius;

            ring.style.strokeDasharray = circumference;
            ring.style.strokeDashoffset = circumference;

            setTimeout(() => {{
                const offset = circumference - (percentage / 100) * circumference;
                ring.style.strokeDashoffset = offset;

                // Animate the number
                let current = 0;
                const target = isNumber ? percentage : percentage;
                const interval = setInterval(() => {{
                    current += isNumber ? 1 : 1;
                    if (current >= target) {{
                        current = target;
                        clearInterval(interval);
                    }}
                    valueEl.textContent = isNumber ? Math.round(current) : Math.round(current) + '%';
                }}, 20);
            }}, 700);
        }}

        // Timeline Gantt
        function generateTimeline() {{
            const timelineContainer = document.getElementById('projectTimeline');
            if (!timelineContainer) return;

            // Real shoots and deadlines data
            const shoots = {shoots_json};
            const deadlines = {deadlines_json};

            // Combine and convert to timeline format
            const now = new Date();
            now.setHours(0, 0, 0, 0);
            const projects = [];

            // Add shoots
            shoots.forEach(shoot => {{
                // Use start_on to due_on range if available, otherwise estimate duration
                let startDate, endDate, duration;

                if (shoot.start_on && shoot.due_on) {{
                    // Project has full date range
                    startDate = new Date(shoot.start_on);
                    endDate = new Date(shoot.due_on);
                }} else if (shoot.start_on) {{
                    // Has start but no due date - use film date as end
                    startDate = new Date(shoot.start_on);
                    endDate = new Date(shoot.datetime);
                }} else if (shoot.due_on) {{
                    // Has due but no start - estimate 5 days before due date
                    const dueDate = new Date(shoot.due_on);
                    startDate = new Date(dueDate);
                    startDate.setDate(startDate.getDate() - 5);
                    endDate = dueDate;
                }} else {{
                    // No date range - estimate 3 days before film date to film date
                    const filmDate = new Date(shoot.datetime);
                    startDate = new Date(filmDate);
                    startDate.setDate(startDate.getDate() - 3);
                    endDate = filmDate;
                }}

                const daysFromNow = Math.floor((startDate - now) / (1000 * 60 * 60 * 24));
                const daysToEnd = Math.floor((endDate - now) / (1000 * 60 * 60 * 24));

                // Only show if it overlaps with the 10-day window
                if (daysToEnd >= 0 && daysFromNow < 10) {{
                    const start = Math.max(0, daysFromNow);
                    const end = Math.min(10, daysToEnd + 1);
                    duration = end - start;

                    if (duration > 0) {{
                        projects.push({{
                            name: shoot.name,
                            start: start,
                            duration: duration,
                            status: daysFromNow <= 2 ? 'critical' : 'normal'
                        }});
                    }}
                }}
            }});

            // Add deadlines
            deadlines.forEach(deadline => {{
                // Use start_on to due_date range if available, otherwise estimate duration
                let startDate, endDate, duration;

                if (deadline.start_on) {{
                    // Project has start date
                    startDate = new Date(deadline.start_on);
                    endDate = new Date(deadline.due_date);
                }} else {{
                    // No start date - estimate 7 days before due date
                    const dueDate = new Date(deadline.due_date);
                    startDate = new Date(dueDate);
                    startDate.setDate(startDate.getDate() - 7);
                    endDate = dueDate;
                }}

                const daysFromNow = Math.floor((startDate - now) / (1000 * 60 * 60 * 24));
                const daysToEnd = Math.floor((endDate - now) / (1000 * 60 * 60 * 24));

                // Only show if it overlaps with the 10-day window
                if (daysToEnd >= 0 && daysFromNow < 10) {{
                    const start = Math.max(0, daysFromNow);
                    const end = Math.min(10, daysToEnd + 1);
                    duration = end - start;

                    if (duration > 0) {{
                        projects.push({{
                            name: deadline.name,
                            start: start,
                            duration: duration,
                            status: daysToEnd <= 2 ? 'critical' : daysToEnd <= 5 ? 'warning' : 'normal'
                        }});
                    }}
                }}
            }});

            // If no projects, show placeholder
            if (projects.length === 0) {{
                projects.push({{
                    name: 'No upcoming shoots or deadlines in next 10 days',
                    start: 0,
                    duration: 10,
                    status: 'normal'
                }});
            }}

            const totalDays = 10;
            const dates = [];
            for (let i = 0; i < totalDays; i++) {{
                const date = new Date();
                date.setDate(date.getDate() + i);
                dates.push(date.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }}));
            }}

            let html = '<div class="timeline-header">';
            html += '<div class="timeline-project-col">Project</div>';
            html += '<div class="timeline-dates">';
            dates.forEach(date => {{
                html += `<div class="timeline-date">${{date}}</div>`;
            }});
            html += '</div></div>';

            projects.forEach(project => {{
                html += '<div class="timeline-row">';
                html += `<div class="timeline-project-name">${{project.name}}</div>`;
                html += '<div class="timeline-bars">';
                const leftPercent = (project.start / totalDays) * 100;
                const widthPercent = (project.duration / totalDays) * 100;
                html += `<div class="timeline-bar ${{project.status}}" style="left: ${{leftPercent}}%; width: ${{widthPercent}}%">${{project.duration}}d</div>`;
                html += '</div></div>';
            }});

            timelineContainer.innerHTML = html;
        }}

        // Radar Chart
        function generateRadarChart() {{
            const container = document.getElementById('radarChart');
            if (!container) return;

            const size = 600;
            const center = size / 2;
            const maxRadius = 200;
            const numLevels = 5;

            // Real category allocation data
            const categories = {radar_categories_json};

            let svg = `<svg class="radar-svg" viewBox="0 0 ${{size}} ${{size}}" width="${{size}}" height="${{size}}">`;

            for (let i = 1; i <= numLevels; i++) {{
                const r = (maxRadius / numLevels) * i;
                svg += `<circle class="radar-grid" cx="${{center}}" cy="${{center}}" r="${{r}}"/>`;
            }}

            const angleStep = (Math.PI * 2) / categories.length;
            categories.forEach((cat, i) => {{
                const angle = angleStep * i - Math.PI / 2;
                const x = center + maxRadius * Math.cos(angle);
                const y = center + maxRadius * Math.sin(angle);
                svg += `<line class="radar-axis" x1="${{center}}" y1="${{center}}" x2="${{x}}" y2="${{y}}"/>`;

                const labelX = center + (maxRadius + 50) * Math.cos(angle);
                const labelY = center + (maxRadius + 50) * Math.sin(angle);
                svg += `<text class="radar-label" x="${{labelX}}" y="${{labelY}}" dy="5">${{cat.name}}</text>`;
            }});

            let targetPoints = '';
            categories.forEach((cat, i) => {{
                const angle = angleStep * i - Math.PI / 2;
                const r = (cat.target / 100) * maxRadius;
                const x = center + r * Math.cos(angle);
                const y = center + r * Math.sin(angle);
                targetPoints += `${{x}},${{y}} `;
            }});
            svg += `<polygon class="radar-target" points="${{targetPoints}}"/>`;

            let actualPoints = '';
            categories.forEach((cat, i) => {{
                const angle = angleStep * i - Math.PI / 2;
                const r = (cat.actual / 100) * maxRadius;
                const x = center + r * Math.cos(angle);
                const y = center + r * Math.sin(angle);
                actualPoints += `${{x}},${{y}} `;
            }});
            svg += `<polygon class="radar-area" points="${{actualPoints}}"/>`;

            svg += '</svg>';
            container.innerHTML = svg;
        }}

        // Velocity Chart
        function generateVelocityChart() {{
            console.log('=== generateVelocityChart called ===');

            // Destroy existing chart if it exists
            if (window.velocityChart) {{
                console.log('Destroying existing velocity chart');
                try {{
                    window.velocityChart.destroy();
                }} catch (e) {{
                    console.log('Error destroying velocity chart:', e);
                }}
                window.velocityChart = null;
            }}

            const canvas = document.getElementById('velocityChart');
            console.log('Velocity chart element found:', !!canvas);

            if (!canvas) return;

            // Force refresh container dimensions before creating chart
            const container = canvas.parentElement;
            if (container) {{
                container.style.display = 'block';
                container.style.visibility = 'visible';

                // Trigger reflow to ensure dimensions are calculated
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                console.log('Velocity container dimensions:', width, 'x', height);
            }}

            // Use actual weekly completion data
            const weeklyData = {weekly_completions_json};

            // Calculate appropriate Y-axis maximum with headroom
            const maxValue = Math.max(...weeklyData);
            const suggestedMax = Math.max(6, Math.ceil(maxValue * 1.3)); // At least 6, or 30% above max value
            const stepSize = suggestedMax <= 10 ? 1 : Math.ceil(suggestedMax / 8); // Use step of 1 for small ranges


            const ctx = canvas.getContext('2d');
            window.velocityChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                    datasets: [{{
                        label: 'Projects Completed',
                        data: weeklyData,
                        borderColor: '#60BBE9',
                        backgroundColor: 'rgba(96, 187, 233, 0.2)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointBackgroundColor: '#60BBE9',
                        pointBorderColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary') || '#fff',
                        pointBorderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    resizeDelay: 0,
                    devicePixelRatio: window.devicePixelRatio || 1,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            suggestedMax: suggestedMax,
                            ticks: {{
                                stepSize: stepSize,
                                color: getChartTextColor(),
                                callback: function(value) {{
                                    if (Number.isInteger(value)) {{
                                        return value;
                                    }}
                                }}
                            }},
                            grid: {{ color: getChartGridColor() }}
                        }},
                        x: {{ ticks: {{ color: getChartTextColor() }}, grid: {{ color: getChartGridColor() }} }}
                    }}
                }}
            }});

            console.log('Velocity chart created successfully:', !!window.velocityChart);
        }}

        // Initialize capacity history chart on page load
        document.addEventListener('DOMContentLoaded', function() {{
            generateCapacityHistoryChart();
        }});

        // Initialize other charts
        document.addEventListener('DOMContentLoaded', () => {{
            setTimeout(() => {{
                animateProgressRing('ringOnTime', 'ringOnTimeValue', {delivery_metrics['on_time_rate']:.0f});
                animateProgressRing('ringUtilization', 'ringUtilizationValue', {team_utilization_avg:.0f});
                animateProgressRing('ringProjects', 'ringProjectsValue', {total_tasks}, true);

                generateTimeline();
                generateRadarChart();
                generateVelocityChart();
            }}, 100);
        }});

        // Theme Toggle Functionality
        function toggleTheme() {{
            const root = document.documentElement;
            const currentTheme = root.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            root.setAttribute('data-theme', newTheme);

            // Update toggle button
            const themeText = document.getElementById('themeText');

            if (newTheme === 'dark') {{
                themeText.textContent = 'Light Mode';
            }} else {{
                themeText.textContent = 'Dark Mode';
            }}

            // Store preference in localStorage
            localStorage.setItem('theme', newTheme);

            // Refresh charts to update text colors
            if (typeof window.capacityHistoryChart !== 'undefined') {{
                window.capacityHistoryChart.destroy();
            }}

            // Regenerate charts with new theme colors
            setTimeout(() => {{
                generateRadarChart();
                generateVelocityChart();
                generateCapacityHistoryChart();

                // Immediate and aggressive mobile recovery
                if (window.innerWidth <= 768) {{
                    console.log('Immediate mobile capacity chart check');
                    // Multiple immediate checks
                    setTimeout(() => ensureMobileCapacityChart(), 50);
                    setTimeout(() => ensureMobileCapacityChart(), 150);
                    setTimeout(() => ensureMobileCapacityChart(), 300);
                    setTimeout(() => ensureMobileCapacityChart(), 600);
                    setTimeout(() => ensureMobileCapacityChart(), 1000);
                }}
            }}, 100);

            // Enhanced mobile-specific fallback after theme change
            const isMobile = window.innerWidth <= 768;
            if (isMobile) {{
                console.log('Mobile device detected during theme toggle');

                // Multiple fallback attempts with increasing delays
                setTimeout(() => {{
                    console.log('Mobile theme fallback attempt 1 (300ms)');
                    ensureMobileCapacityChart();
                }}, 300);

                setTimeout(() => {{
                    console.log('Mobile theme fallback attempt 2 (600ms)');
                    ensureMobileCapacityChart();
                }}, 600);

                setTimeout(() => {{
                    console.log('Mobile theme fallback attempt 3 (1000ms)');
                    ensureMobileCapacityChart();
                }}, 1000);
            }}
        }}

        // Simplified chart helper function
        function ensureMobileCapacityChart() {{
            const chartElement = document.getElementById('capacityHistoryChart');
            if (chartElement && !window.capacityHistoryChart) {{
                console.log('Creating missing capacity chart');
                generateCapacityHistoryChart();
            }}
        }}

        // Initialize theme from localStorage
        function initializeTheme() {{
            const storedTheme = localStorage.getItem('theme') || 'light';
            const root = document.documentElement;

            root.setAttribute('data-theme', storedTheme);

            // Update toggle button to match
            const themeText = document.getElementById('themeText');

            if (storedTheme === 'dark') {{
                themeText.textContent = 'Light Mode';
            }} else {{
                themeText.textContent = 'Dark Mode';
            }}
        }}

        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', initializeTheme);

        // Navigation functionality
        function initializeNavigation() {{
            // Add smooth scrolling to nav links
            document.querySelectorAll('.nav-link').forEach(link => {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const targetId = this.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);

                    if (targetElement) {{
                        const navHeight = document.querySelector('.sticky-nav').offsetHeight;
                        const targetPosition = targetElement.offsetTop - navHeight - 20;

                        window.scrollTo({{
                            top: targetPosition,
                            behavior: 'smooth'
                        }});

                        // Update active state
                        updateActiveNavLink(targetId);
                    }}
                }});
            }});

            // Update active nav link on scroll
            window.addEventListener('scroll', throttle(updateActiveNavOnScroll, 100));
        }}

        function updateActiveNavLink(activeId) {{
            document.querySelectorAll('.nav-link').forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${{activeId}}`) {{
                    link.classList.add('active');
                }}
            }});
        }}

        function updateActiveNavOnScroll() {{
            const sections = ['overview', 'capacity', 'metrics', 'deadlines', 'forecasts', 'analytics'];
            const navHeight = document.querySelector('.sticky-nav').offsetHeight;
            const scrollPos = window.scrollY + navHeight + 50;

            for (let i = sections.length - 1; i >= 0; i--) {{
                const section = document.getElementById(sections[i]);
                if (section && section.offsetTop <= scrollPos) {{
                    updateActiveNavLink(sections[i]);
                    break;
                }}
            }}
        }}

        function throttle(func, limit) {{
            let lastFunc;
            let lastRan;
            return function() {{
                const context = this;
                const args = arguments;
                if (!lastRan) {{
                    func.apply(context, args);
                    lastRan = Date.now();
                }} else {{
                    clearTimeout(lastFunc);
                    lastFunc = setTimeout(function() {{
                        if ((Date.now() - lastRan) >= limit) {{
                            func.apply(context, args);
                            lastRan = Date.now();
                        }}
                    }}, limit - (Date.now() - lastRan));
                }}
            }}
        }}

        // Initialize navigation when DOM is ready
        document.addEventListener('DOMContentLoaded', initializeNavigation);

        // Keyboard Navigation Support
        function setupKeyboardNavigation() {{
            // Add keyboard support for team members
            document.querySelectorAll('.team-member[tabindex="0"]').forEach(member => {{
                member.addEventListener('keydown', function(e) {{
                    if (e.key === 'Enter' || e.key === ' ') {{
                        e.preventDefault();
                        // Future: Could expand team member details or navigate to detailed view
                        member.focus();
                        member.style.outline = '2px solid var(--brand-primary)';
                        setTimeout(() => {{
                            member.style.outline = '';
                        }}, 1000);
                    }}
                }});
            }});

            // Skip links for better navigation
            const skipLink = document.createElement('a');
            skipLink.href = '#dashboard-title';
            skipLink.textContent = 'Skip to main content';
            skipLink.className = 'sr-only';
            skipLink.style.position = 'absolute';
            skipLink.style.top = '10px';
            skipLink.style.left = '10px';
            skipLink.style.zIndex = '9999';
            skipLink.addEventListener('focus', function() {{
                this.classList.remove('sr-only');
                this.style.background = 'var(--brand-primary)';
                this.style.color = 'white';
                this.style.padding = '8px 12px';
                this.style.textDecoration = 'none';
                this.style.borderRadius = '4px';
            }});
            skipLink.addEventListener('blur', function() {{
                this.classList.add('sr-only');
            }});

            document.body.insertBefore(skipLink, document.body.firstChild);
        }}

        // Initialize keyboard navigation
        document.addEventListener('DOMContentLoaded', setupKeyboardNavigation);

        // Interactive Features
        function setupInteractiveFeatures() {{
            // Add enhanced tooltips for metrics
            document.querySelectorAll('.metric-value').forEach(metric => {{
                const label = metric.parentElement.querySelector('.metric-label')?.textContent || 'Metric';
                const value = metric.textContent;

                if (!metric.hasAttribute('data-tooltip')) {{
                    metric.classList.add('tooltip');
                    metric.setAttribute('data-tooltip', `${{label}}: ${{value}}`);
                }}
            }});

            // Add click handlers for team members
            document.querySelectorAll('.team-member').forEach(member => {{
                member.addEventListener('click', function() {{
                    // Highlight selected member
                    document.querySelectorAll('.team-member').forEach(m => m.classList.remove('selected'));
                    this.classList.add('selected');

                    // Add selection styling
                    this.style.outline = '2px solid var(--brand-primary)';
                    this.style.outlineOffset = '2px';

                    // Future: Could expand to show detailed task breakdown
                }});
            }});

            // Add chart interaction (basic hover effects)
            document.querySelectorAll('.progress-ring').forEach(ring => {{
                ring.addEventListener('mouseenter', function() {{
                    this.style.transform = 'scale(1.05)';
                    this.style.transition = 'transform 0.3s ease';
                }});

                ring.addEventListener('mouseleave', function() {{
                    this.style.transform = 'scale(1)';
                }});
            }});

            // Add smooth scroll to sections
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});

            // Add card focus effects
            document.querySelectorAll('.card').forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transition = 'all 0.3s ease';
                }});
            }});
        }}

        // Table sorting functionality (if tables exist)
        function setupTableSorting() {{
            document.querySelectorAll('.sortable').forEach(header => {{
                header.addEventListener('click', function() {{
                    const table = this.closest('table');
                    const tbody = table.querySelector('tbody');
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const columnIndex = Array.from(this.parentNode.children).indexOf(this);

                    // Toggle sort direction
                    const isAsc = this.classList.contains('asc');

                    // Reset all headers
                    table.querySelectorAll('.sortable').forEach(h => {{
                        h.classList.remove('asc', 'desc');
                    }});

                    // Set current header
                    this.classList.add(isAsc ? 'desc' : 'asc');

                    // Sort rows
                    rows.sort((a, b) => {{
                        const aText = a.cells[columnIndex].textContent.trim();
                        const bText = b.cells[columnIndex].textContent.trim();

                        // Try numeric sort first
                        const aNum = parseFloat(aText);
                        const bNum = parseFloat(bText);

                        if (!isNaN(aNum) && !isNaN(bNum)) {{
                            return isAsc ? bNum - aNum : aNum - bNum;
                        }} else {{
                            return isAsc ? bText.localeCompare(aText) : aText.localeCompare(bText);
                        }}
                    }});

                    // Reorder table
                    rows.forEach(row => tbody.appendChild(row));
                }});
            }});
        }}

        // Export Functions
        function exportToPDF() {{
            // Create a new window with print-friendly styles
            const printWindow = window.open('', '_blank');
            const currentContent = document.documentElement.outerHTML;

            // CSS for print - CLEAN DATA-ONLY VERSION
            const printCSS = `
                <style>
                    @media print {{
                        * {{
                            box-shadow: none !important;
                            animation: none !important;
                            transition: none !important;
                        }}

                        body {{
                            background: white !important;
                            color: black !important;
                            padding: 15px !important;
                            font-family: Arial, sans-serif !important;
                            font-size: 11px !important;
                            line-height: 1.3 !important;
                        }}

                        /* Hide all visual elements - keep only data */
                        .header-controls,
                        .theme-toggle,
                        .export-btn,
                        .chart-container,
                        canvas,
                        .timeline-container,
                        .project-timeline,
                        .progress-ring,
                        .capacity-bar,
                        .progress-fill {{
                            display: none !important;
                        }}

                        /* Clean header */
                        .header {{
                            padding: 0 !important;
                            margin-bottom: 15px !important;
                            text-align: center !important;
                            border-bottom: 2px solid #333 !important;
                            padding-bottom: 10px !important;
                        }}

                        .header h1 {{
                            font-size: 18px !important;
                            margin: 0 !important;
                            font-weight: bold !important;
                        }}

                        .header .subtitle {{
                            font-size: 10px !important;
                            margin: 2px 0 !important;
                            color: #666 !important;
                        }}

                        .header .timestamp {{
                            font-size: 9px !important;
                            margin: 2px 0 !important;
                            color: #888 !important;
                        }}

                        /* Clean, organized sections */
                        .card {{
                            margin: 8px 0 !important;
                            padding: 10px !important;
                            background: white !important;
                            border: 1px solid #ccc !important;
                            break-inside: avoid !important;
                            page-break-inside: avoid !important;
                        }}

                        .card h2 {{
                            font-size: 14px !important;
                            margin: 0 0 8px 0 !important;
                            color: #333 !important;
                            font-weight: bold !important;
                            border-bottom: 1px solid #eee !important;
                            padding-bottom: 4px !important;
                        }}

                        /* Two-column layout for main sections */
                        .performance-row {{
                            display: grid !important;
                            grid-template-columns: 1fr 1fr !important;
                            gap: 15px !important;
                            margin-bottom: 15px !important;
                        }}

                        /* Clean metrics display */
                        .metric {{
                            margin: 4px 0 !important;
                            display: flex !important;
                            justify-content: space-between !important;
                            padding: 2px 0 !important;
                            border-bottom: 1px dotted #ddd !important;
                        }}

                        .metric-label {{
                            font-size: 10px !important;
                            color: #555 !important;
                        }}

                        .metric-value {{
                            font-size: 11px !important;
                            font-weight: bold !important;
                            color: #000 !important;
                        }}

                        /* Team capacity as clean list */
                        .team-member {{
                            margin: 6px 0 !important;
                            padding: 6px !important;
                            border: 1px solid #ddd !important;
                            background: #f9f9f9 !important;
                        }}

                        .team-member-name {{
                            font-size: 10px !important;
                            font-weight: bold !important;
                            margin-bottom: 3px !important;
                        }}

                        /* Category table - clean and readable */
                        table {{
                            width: 100% !important;
                            border-collapse: collapse !important;
                            margin: 8px 0 !important;
                            font-size: 9px !important;
                        }}

                        th, td {{
                            padding: 4px 6px !important;
                            border: 1px solid #ccc !important;
                            text-align: left !important;
                        }}

                        th {{
                            background: #f0f0f0 !important;
                            font-weight: bold !important;
                            font-size: 9px !important;
                        }}

                        /* At-risk tasks - clean list */
                        .project-card {{
                            margin: 6px 0 !important;
                            padding: 6px !important;
                            border: 1px solid #ddd !important;
                            background: #fafafa !important;
                            break-inside: avoid !important;
                        }}

                        .project-card-title {{
                            font-size: 10px !important;
                            font-weight: bold !important;
                            margin-bottom: 3px !important;
                        }}

                        .project-card-date {{
                            font-size: 9px !important;
                            color: #666 !important;
                        }}

                        /* Page settings */
                        @page {{
                            margin: 0.75in;
                            size: letter;
                        }}

                        /* Simple single-column layout */
                        .dashboard-container {{
                            display: block !important;
                        }}

                        /* Hide grid layouts that cause issues */
                        .grid {{
                            display: block !important;
                        }}

                        .grid .card {{
                            margin-bottom: 10px !important;
                        }}
                    }}
                </style>
            `;

            printWindow.document.write(currentContent.replace('</head>', printCSS + '</head>'));
            printWindow.document.close();

            setTimeout(() => {{
                printWindow.print();
                printWindow.close();
            }}, 500);
        }}

        function exportToCSV() {{
            const data = [];

            // Add header
            data.push(['Dashboard Export', 'Generated: ' + new Date().toLocaleString()]);
            data.push([]); // Empty row

            // Extract team capacity data
            data.push(['Team Member', 'Current Allocation', 'Max Capacity', 'Utilization %']);

            document.querySelectorAll('.team-member').forEach(member => {{
                const name = member.querySelector('.team-member-name')?.textContent || 'Unknown';
                const capacity = member.querySelector('.team-member-capacity')?.textContent || '';
                const tooltip = member.getAttribute('data-tooltip') || '';

                // Parse capacity text (e.g., "75% / 100% capacity")
                const capacityMatch = capacity.match(/(\\d+(?:\\.\\d+)?)%\\s*\\/\\s*(\\d+(?:\\.\\d+)?)%/);
                if (capacityMatch) {{
                    const current = capacityMatch[1];
                    const max = capacityMatch[2];
                    const utilization = ((parseFloat(current) / parseFloat(max)) * 100).toFixed(1);

                    data.push([name, current + '%', max + '%', utilization + '%']);
                }}
            }});

            data.push([]); // Empty row

            // Extract metrics
            data.push(['Performance Metrics', 'Value']);
            document.querySelectorAll('.metric').forEach(metric => {{
                const label = metric.querySelector('.metric-label')?.textContent || '';
                const value = metric.querySelector('.metric-value')?.textContent || '';
                if (label && value) {{
                    data.push([label.trim(), value.trim()]);
                }}
            }});

            // Convert to CSV
            const csvContent = data.map(row =>
                row.map(field => `"${{field.toString().replace(/"/g, '""')}}"`)
                   .join(',')
            ).join('\\n');

            // Download file
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `perimeter-studio-dashboard-${{new Date().toISOString().split('T')[0]}}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        // Initialize interactive features
        document.addEventListener('DOMContentLoaded', function() {{
            setupInteractiveFeatures();
            setupTableSorting();
        }});

        // Handle window resize for responsive charts
        let resizeTimeout;
        window.addEventListener('resize', function() {{
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {{
                console.log('=== Window resize triggered ===');
                console.log('New window size:', window.innerWidth, 'x', window.innerHeight);

                // Check if Historical Capacity chart exists before destroying
                const chartElement = document.getElementById('capacityHistoryChart');
                console.log('Chart element exists:', !!chartElement);
                console.log('Chart element dimensions:', chartElement ? chartElement.offsetWidth + 'x' + chartElement.offsetHeight : 'N/A');

                // Regenerate charts with improved error handling
                if (window.capacityHistoryChart) {{
                    console.log('Destroying existing Historical Capacity chart');
                    try {{
                        window.capacityHistoryChart.destroy();
                        window.capacityHistoryChart = null;
                    }} catch (e) {{
                        console.error('Error destroying chart:', e);
                    }}
                }}

                // Regenerate all charts with staggered timing to avoid conflicts
                setTimeout(() => {{
                    try {{
                        generateRadarChart();
                    }} catch (e) {{
                        console.error('Error generating radar chart:', e);
                    }}
                }}, 50);

                setTimeout(() => {{
                    try {{
                        generateVelocityChart();
                    }} catch (e) {{
                        console.error('Error generating velocity chart:', e);
                    }}
                }}, 100);

                setTimeout(() => {{
                    try {{
                        console.log('Regenerating Historical Capacity chart after resize');
                        generateCapacityHistoryChart();
                    }} catch (e) {{
                        console.error('Error generating capacity history chart:', e);
                    }}
                }}, 150);
            }}, 350);
        }});

        // Optimize touch interactions for mobile
        if ('ontouchstart' in window) {{
            document.body.classList.add('touch-device');

            // Improve chart tooltips for touch devices
            const style = document.createElement('style');
            style.textContent = `
                .touch-device .chart-container {{
                    -webkit-tap-highlight-color: transparent;
                }}
                .touch-device canvas {{
                    touch-action: pan-y;
                }}
            `;
            document.head.appendChild(style);
        }}
        // Add theme change listener to regenerate charts
        function observeThemeChanges() {{
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {{
                        console.log('Theme changed, regenerating charts...');

                        // Regenerate all charts with new theme colors
                        if (window.trendsChart) {{
                            const newTrendColors = getThemeAwareTrendColors();
                            window.trendsChart.data.datasets.forEach((dataset, index) => {{
                                if (index < newTrendColors.length) {{
                                    dataset.borderColor = newTrendColors[index];
                                    dataset.backgroundColor = newTrendColors[index];
                                }}
                            }});

                            // Update axis colors for theme
                            const newTextColor = getChartTextColor();
                            const newGridColor = getChartGridColor();

                            window.trendsChart.options.scales.y.ticks.color = newTextColor;
                            window.trendsChart.options.scales.y.grid.color = newGridColor;
                            window.trendsChart.options.scales.x.ticks.color = newTextColor;
                            window.trendsChart.options.scales.x.grid.color = newGridColor;
                            window.trendsChart.options.plugins.legend.labels.color = newTextColor;

                            window.trendsChart.update();
                        }}

                        if (window.capacityHistoryChart) {{
                            const newMemberColors = getThemeAwareMemberColors();
                            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
                            const newThresholdColor = isDarkMode ? '#FF6B6B' : '#dc3545';

                            window.capacityHistoryChart.data.datasets.forEach((dataset) => {{
                                if (dataset.label === '100% Capacity Threshold') {{
                                    dataset.borderColor = newThresholdColor;
                                }} else if (newMemberColors[dataset.label]) {{
                                    dataset.borderColor = newMemberColors[dataset.label];
                                    dataset.pointBackgroundColor = newMemberColors[dataset.label];
                                    dataset.pointBorderColor = newMemberColors[dataset.label];
                                    if (dataset.label === 'Team Total') {{
                                        dataset.backgroundColor = newMemberColors[dataset.label] + '33';
                                    }}
                                }}
                            }});

                            // Update axis colors for theme
                            const newTextColor = getChartTextColor();
                            const newGridColor = getChartGridColor();

                            if (window.capacityHistoryChart.options.scales.y) {{
                                window.capacityHistoryChart.options.scales.y.ticks.color = newTextColor;
                                window.capacityHistoryChart.options.scales.y.grid.color = newGridColor;
                            }}
                            if (window.capacityHistoryChart.options.scales.x) {{
                                window.capacityHistoryChart.options.scales.x.ticks.color = newTextColor;
                                window.capacityHistoryChart.options.scales.x.grid.color = newGridColor;
                            }}
                            if (window.capacityHistoryChart.options.plugins.legend) {{
                                window.capacityHistoryChart.options.plugins.legend.labels.color = newTextColor;
                            }}

                            // Use 'none' animation for iPad to prevent rendering issues
                            const isTablet = window.innerWidth >= 768 && window.innerWidth <= 1024;
                            const updateOptions = isTablet ? {{ animation: false }} : {{ animation: {{ duration: 300 }} }};

                            window.capacityHistoryChart.update(updateOptions);

                            // Additional iPad-specific fix: Force canvas redraw
                            if (isTablet) {{
                                setTimeout(() => {{
                                    if (window.capacityHistoryChart && window.capacityHistoryChart.canvas) {{
                                        window.capacityHistoryChart.canvas.style.visibility = 'visible';
                                        window.capacityHistoryChart.resize();
                                    }}
                                }}, 100);
                            }}
                        }}

                        if (window.velocityChart) {{
                            // Update axis colors for theme
                            const newTextColor = getChartTextColor();
                            const newGridColor = getChartGridColor();

                            if (window.velocityChart.options.scales.y) {{
                                window.velocityChart.options.scales.y.ticks.color = newTextColor;
                                window.velocityChart.options.scales.y.grid.color = newGridColor;
                            }}
                            if (window.velocityChart.options.scales.x) {{
                                window.velocityChart.options.scales.x.ticks.color = newTextColor;
                                window.velocityChart.options.scales.x.grid.color = newGridColor;
                            }}
                            if (window.velocityChart.options.plugins.legend) {{
                                window.velocityChart.options.plugins.legend.labels.color = newTextColor;
                            }}

                            window.velocityChart.update();
                        }}
                    }}
                }});
            }});

            observer.observe(document.documentElement, {{
                attributes: true,
                attributeFilter: ['data-theme']
            }});
        }}

        // Start observing theme changes
        observeThemeChanges();
"""

    html += """
    </script>

        </main>
    </div>
</body>
</html>
"""

    # Save HTML dashboard
    output_file = 'Reports/capacity_dashboard.html'
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"HTML dashboard generated: {output_file}")
    return output_file

def generate_html_dashboard_jinja2(data):
    """Generate HTML dashboard using Jinja2 templates"""

    # Set up Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))

    # Prepare data context for templates
    context = {
        'data': data,
        'total_tasks': data.get('active_task_count', 0),
        'team_capacity': data.get('team_capacity', []),
        'upcoming_shoots': data.get('upcoming_shoots', []),
        'upcoming_deadlines': data.get('upcoming_deadlines', []),
        'forecasted_projects': data.get('forecasted_projects', []),
        'delivery_log': data.get('delivery_log'),
        'variance_data': data.get('variance'),
        'capacity_history': data.get('capacity_history_by_member', {}),
        'external_projects': data.get('external_projects', []),
    }

    # Calculate additional metrics for templates
    delivery_metrics = calculate_delivery_metrics(data)
    context['delivery_metrics'] = delivery_metrics

    # Render main dashboard template
    template = env.get_template('dashboard.html')
    html = template.render(**context)

    # Save HTML dashboard
    output_file = 'Reports/capacity_dashboard.html'
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"HTML dashboard generated: {output_file}")
    return output_file

def calculate_delivery_metrics(data):
    """Extract delivery metrics for templates"""
    metrics = {
        'total_completed': 0,
        'completed_this_year': 0,
        'on_time_rate': 0,
        'avg_capacity_variance': 0,
    }

    if data.get('delivery_log') is not None:
        df = data['delivery_log']
        metrics['total_completed'] = len(df)

        # Calculate this year's completions
        current_year = datetime.now().year
        tasks_with_completion = df[df['Completed Date'].notna()]
        completed_this_year = 0

        for _, task in tasks_with_completion.iterrows():
            try:
                completion_date = pd.to_datetime(task['Completed Date'])
                if completion_date.year == current_year:
                    completed_this_year += 1
            except:
                pass

        metrics['completed_this_year'] = completed_this_year

        # Calculate on-time rate
        on_time_count = len(df[df['Status'] == 'On Time']) if 'Status' in df.columns else 0
        metrics['on_time_rate'] = (on_time_count / len(df) * 100) if len(df) > 0 else 0

    return metrics

def main():
    """Main dashboard generation function"""
    print("Generating Perimeter Studio Dashboard...")

    # Read report data
    data = read_reports()

    # Generate HTML dashboard
    html_file = generate_html_dashboard(data)

    print(f"\nDashboard generation complete!")
    print(f"HTML: {html_file}")

if __name__ == "__main__":
    main()
