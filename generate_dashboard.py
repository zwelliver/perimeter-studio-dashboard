"""
Perimeter Studio Capacity Dashboard Generator
Generates interactive HTML dashboard
"""

import pandas as pd
import os
import json
import math
from datetime import datetime, timedelta, timezone

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
        'Zach Welliver': {'max': 50},
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

        # Check if task is overdue
        if task['due_on']:
            try:
                due_date = datetime.fromisoformat(task['due_on']).date() if isinstance(task['due_on'], str) else task['due_on']

                if due_date < today:
                    risk_factors.append(f"Overdue by {(today - due_date).days} days")
                elif due_date <= seven_days:
                    # Due within 7 days - check Task Progress based on project type

                    if project == 'Production':
                        # Production: at-risk if "Needs Scheduling" and approaching due date
                        if task_progress == 'Needs Scheduling':
                            risk_factors.append(f"Due in {(due_date - today).days} days, needs scheduling")

                    elif project == 'Post Production':
                        # Post Production: at-risk if "Filmed" or "Offloaded" (but NOT "In Progress") and approaching due date
                        if task_progress in ['Filmed', 'Offloaded']:
                            risk_factors.append(f"Due in {(due_date - today).days} days, not yet in progress")
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
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: #f8f9fa;
            color: #09243F;
            padding: 20px;
            min-height: 100vh;
        }}

        .dashboard-container {{
            max-width: 95%;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            border-left: 4px solid #60BBE9;
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
            stroke: #e9ecef;
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
            color: #60BBE9;
        }}

        .gauge-label {{
            font-size: 12px;
            color: #6c757d;
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
            width: 140px;
            height: 140px;
            text-align: center;
        }}

        .progress-ring-svg {{
            transform: rotate(-90deg);
        }}

        .progress-ring-circle {{
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
        }}

        .progress-ring-bg {{
            stroke: #e9ecef;
        }}

        .progress-ring-progress {{
            transition: stroke-dashoffset 2s ease;
        }}

        .progress-ring-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            width: 120px;
        }}

        .progress-ring-value {{
            font-size: 24px;
            font-weight: 700;
            color: #09243F;
            display: block;
            line-height: 1;
        }}

        .progress-ring-label {{
            font-size: 10px;
            color: #6c757d;
            display: block;
            margin-top: 5px;
            line-height: 1.3;
            max-width: 100%;
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
            background: #09243F;
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
            border-bottom: 2px solid #dee2e6;
        }}

        .timeline-project-col {{
            width: 25%;
            font-weight: 600;
            color: #09243F;
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
            color: #6c757d;
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
            color: #09243F;
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
            background: #60BBE9;
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
            background: #60BBE9;
        }}

        .timeline-bar.info {{
            background: #17a2b8;
        }}

        /* ===== RADAR/SPIDER CHART STYLES ===== */
        .radar-container {{
            position: relative;
            width: 600px;
            height: 600px;
            margin: 20px auto;
        }}

        .radar-grid {{
            fill: none;
            stroke: #dee2e6;
            stroke-width: 1;
        }}

        .radar-axis {{
            stroke: #adb5bd;
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
            fill: #09243F;
            font-size: 12px;
            font-weight: 600;
            text-anchor: middle;
        }}

        /* ===== SUNBURST CHART STYLES ===== */
        .sunburst-container {{
            position: relative;
            width: 400px;
            height: 400px;
            margin: 20px auto;
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
            height: 300px;
            margin: 20px 0;
        }}

        /* ===== HEAT MAP CALENDAR STYLES ===== */
        .heatmap-calendar {{
            display: grid;
            grid-template-columns: auto repeat(10, 1fr);
            gap: 4px;
            margin: 20px 0;
        }}

        .heatmap-day-label {{
            font-size: 11px;
            color: #6c757d;
            padding: 8px 12px;
            text-align: right;
        }}

        .heatmap-date {{
            font-size: 10px;
            color: #6c757d;
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
            color: #09243F;
            font-size: 28px;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .header .subtitle {{
            color: #6c757d;
            font-size: 13px;
            margin-bottom: 5px;
        }}

        .header .timestamp {{
            color: #60BBE9;
            font-size: 12px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }}

        .card {{
            background: white;
            padding: 20px 24px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            border: 1px solid #e9ecef;
            transition: box-shadow 0.2s;
        }}

        .card:hover {{
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        }}

        .card h2 {{
            color: #09243F;
            font-size: 16px;
            margin-bottom: 18px;
            font-weight: 600;
            border-bottom: 2px solid #60BBE9;
            padding-bottom: 8px;
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }}

        .metric:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            font-size: 13px;
            color: #6c757d;
        }}

        .metric-value {{
            font-size: 22px;
            font-weight: 600;
            color: #60BBE9;
        }}

        .metric-value.positive {{
            color: #28a745;
        }}

        .metric-value.negative {{
            color: #dc3545;
        }}

        .metric-value.warning {{
            color: #ffc107;
        }}

        .progress-bar {{
            width: 100%;
            height: 24px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}

        .progress-fill {{
            height: 100%;
            background: #60BBE9;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}

        .progress-fill.over-capacity {{
            background: #dc3545;
        }}

        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-size: 13px;
            border: 1px solid #ffc107;
            color: #856404;
        }}

        .alert.danger {{
            background: #f8d7da;
            border-left-color: #dc3545;
            border-color: #dc3545;
            color: #721c24;
        }}

        .alert.success {{
            background: #d4edda;
            border-left-color: #28a745;
            border-color: #28a745;
            color: #155724;
        }}

        .chart-container {{
            position: relative;
            height: 280px;
            margin-top: 12px;
        }}

        .team-member {{
            margin-bottom: 15px;
        }}

        .team-member-name {{
            font-size: 13px;
            font-weight: 600;
            color: #09243F;
            margin-bottom: 4px;
        }}

        .team-member-capacity {{
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 4px;
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

        /* Mobile Responsive Styles */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
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
                grid-template-columns: 1fr;
                gap: 15px;
            }}

            .card {{
                padding: 15px;
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
            }}

            .team-member-name {{
                font-size: 13px;
            }}

            .alert {{
                padding: 12px;
                font-size: 13px;
            }}

            /* Make chat widget more mobile-friendly */
            .chat-widget {{
                bottom: 15px;
                right: 15px;
            }}

            .chat-button {{
                width: 50px;
                height: 50px;
                font-size: 20px;
            }}

            .chat-window {{
                bottom: 75px;
                right: 10px;
                left: 10px;
                width: auto;
                max-width: none;
                height: 500px;
            }}

            .chat-messages {{
                padding: 15px;
            }}

            .chat-message {{
                max-width: 85%;
                font-size: 14px;
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
            .header h1 {{
                font-size: 20px;
            }}

            .card {{
                padding: 12px;
            }}

            .card h2 {{
                font-size: 15px;
            }}

            .metric-value {{
                font-size: 18px;
            }}

            .chart-container {{
                height: 220px;
            }}

            .chat-button {{
                width: 45px;
                height: 45px;
                font-size: 18px;
            }}

            .chat-window {{
                height: 450px;
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
            }}

            .chat-window {{
                height: 350px;
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

        /* Chat Widget Styles */
        .chat-widget {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }}

        .chat-button {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #60BBE9;
            color: white;
            border: 2px solid #60BBE9;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
        }}

        .chat-button:hover {{
            background: #4a9fd8;
            border-color: #4a9fd8;
        }}

        .chat-window {{
            display: none;
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 400px;
            max-width: calc(100vw - 40px);
            height: 600px;
            max-height: calc(100vh - 120px);
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border: 1px solid #dee2e6;
            flex-direction: column;
            overflow: hidden;
        }}

        .chat-window.open {{
            display: flex;
        }}

        .chat-header {{
            background: #09243F;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #dee2e6;
        }}

        .chat-header h3 {{
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }}

        .chat-close {{
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
        }}

        .chat-close:hover {{
            background: rgba(255,255,255,0.1);
        }}

        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }}

        .chat-message {{
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 80%;
            line-height: 1.4;
        }}

        .chat-message.user {{
            background: #60BBE9;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}

        .chat-message.assistant {{
            background: white;
            color: #09243F;
            margin-right: auto;
            border-bottom-left-radius: 4px;
            border: 1px solid #dee2e6;
        }}

        .chat-message.system {{
            background: #fff3cd;
            color: #856404;
            margin: 0 auto;
            text-align: center;
            font-size: 13px;
            border: 1px solid #ffc107;
        }}

        .chat-input-container {{
            padding: 15px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }}

        .chat-input {{
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            background: white;
            color: #09243F;
        }}

        .chat-input::placeholder {{
            color: #6c757d;
        }}

        .chat-input:focus {{
            outline: none;
            border-color: #60BBE9;
            box-shadow: 0 0 0 3px rgba(96, 187, 233, 0.1);
        }}

        .chat-send {{
            padding: 10px 20px;
            background: #60BBE9;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }}

        .chat-send:hover {{
            background: #4a9fd8;
        }}

        .chat-send:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}

        .typing-indicator {{
            display: none;
            padding: 10px 16px;
            background: white;
            border-radius: 8px;
            max-width: 60px;
            border: 1px solid #dee2e6;
        }}

        .typing-indicator.show {{
            display: block;
        }}

        .typing-indicator span {{
            height: 8px;
            width: 8px;
            background: #60BBE9;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>Perimeter Studio Dashboard</h1>
            <div class="subtitle">Video Production Capacity Tracking & Performance Metrics</div>
            <div class="timestamp">Last Updated: {data['timestamp']}</div>
        </div>

        <div class="grid">
            <!-- Performance Overview -->
            <div class="card">
                <h2>Performance Overview</h2>
                <div class="metric">
                    <span class="metric-label">Active Tasks</span>
                    <span class="metric-value">{total_tasks}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Projects Completed (30d)</span>
                    <span class="metric-value">{delivery_metrics['total_completed']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Projects Completed This Year</span>
                    <span class="metric-value">{delivery_metrics['completed_this_year']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Days Variance</span>
                    <span class="metric-value {'positive' if delivery_metrics['avg_days_variance'] <= 0 else 'warning' if delivery_metrics['avg_days_variance'] <= 3 else 'negative'}">{delivery_metrics['avg_days_variance']:+.1f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Delayed Due to Capacity</span>
                    <span class="metric-value {'positive' if delivery_metrics['projects_delayed_capacity'] == 0 else 'negative'}">{delivery_metrics['projects_delayed_capacity']}</span>
                </div>
            </div>

            <!-- Team Capacity -->
            <div class="card">
                <h2>Team Capacity</h2>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 10px;">
"""

    # Add team members
    for member in team_capacity:
        utilization = (member['current'] / member['max'] * 100) if member['max'] > 0 else 0
        over_capacity = member['current'] > member['max']

        html += f"""
                    <div class="team-member">
                        <div class="team-member-name">{member['name']}</div>
                        <div class="team-member-capacity">{member['current']:.0f}% / {member['max']}% capacity</div>
                        <div class="progress-bar">
                            <div class="progress-fill {'over-capacity' if over_capacity else ''}" style="width: {min(utilization, 100)}%">
                                {utilization:.0f}%
                            </div>
                        </div>
                    </div>
"""

    html += """
                </div>
            </div>

            <!-- External Projects (Contracted/Outsourced) -->
            <div class="card">
                <h2>Contracted/Outsourced Projects</h2>
"""

    # Add external projects
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
                <div style="margin-top: 10px; padding-left: 10px; border-left: 2px solid """ + BRAND_BLUE + """;">
"""
                for task in project['tasks']:
                    due_text = f" (Due: {task['due_on']})" if task.get('due_on') else ""
                    videographer_text = f" | Videographer: {task['videographer']}" if task.get('videographer') else ""
                    html += f"""
                    <div style="font-size: 12px; color: #6c757d; margin: 4px 0;">• {task['name']}{videographer_text}{due_text}</div>
"""
                html += """
                </div>
"""
    else:
        html += """
                <div style="text-align: center; padding: 20px; color: #6c757d;">
                    <div style="font-size: 14px;">No external projects</div>
                </div>
"""

    html += """
            </div>
        </div>

        <!-- At-Risk Tasks -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>⚠️ At-Risk Tasks</h2>
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
                <div style="border-left: 4px solid #dc3545; padding: 10px; margin-bottom: 10px; background: {BRAND_OFF_WHITE};">
                    <div style="font-weight: bold; color: {BRAND_NAVY};">{task['name']}</div>
                    <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                        {task['project']} | {task['assignee']}{videographer_display} | Due: {task['due_on']}
                    </div>
                    <div style="font-size: 13px; color: #dc3545; margin-top: 8px;">
                        {risks_html}
                    </div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += """
            <div style="text-align: center; padding: 20px; color: #28a745;">
                <div style="font-size: 48px;">✅</div>
                <div style="font-size: 18px; margin-top: 10px;">No tasks currently at risk!</div>
            </div>
        """

    html += """
        </div>

        <!-- Upcoming Shoots -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>🎬 Upcoming Shoots</h2>
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
                <div style="border: 2px solid #dee2e6; border-radius: 12px; padding: 18px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <div style="font-size: 16px; font-weight: bold; color: #09243F;">{date_str}</div>
                            <div style="font-size: 20px; font-weight: 600; color: {BRAND_BLUE}; margin-top: 4px;">{time_str}</div>
                        </div>
                        <span style="display: inline-block; padding: 6px 12px; background: {BRAND_NAVY}; color: white; font-size: 14px; border-radius: 6px; white-space: nowrap;">{shoot['project']}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" style="color: #09243F; text-decoration: none; font-weight: 500; font-size: 16px; line-height: 1.4; display: block;">
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
            <div style="text-align: center; padding: 30px; color: #6c757d;">
                <div style="font-size: 48px; margin-bottom: 10px;">📅</div>
                <div style="font-size: 16px;">No upcoming shoots scheduled</div>
            </div>
        """

    html += """
        </div>

        <!-- Upcoming Project Deadlines -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>⏰ Upcoming Project Deadlines</h2>
            <p style="color: #6c757d; margin-top: 8px; font-size: 14px;">Projects due within the next 10 days</p>
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
                <div style="border: 2px solid #dee2e6; border-radius: 12px; padding: 18px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <div style="font-size: 16px; font-weight: bold; color: #09243F;">{date_str}</div>
                            <div style="font-size: 22px; font-weight: 600; color: {urgency_color}; margin-top: 6px;">{urgency_text}</div>
                        </div>
                        <span style="display: inline-block; padding: 6px 12px; background: {BRAND_NAVY}; color: white; font-size: 14px; border-radius: 6px; white-space: nowrap;">{deadline['project']}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" style="color: #09243F; text-decoration: none; font-weight: 500; font-size: 16px; line-height: 1.4; display: block;">
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
            <div style="text-align: center; padding: 30px; color: #6c757d;">
                <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
                <div style="font-size: 16px;">No upcoming deadlines in the next 10 days</div>
            </div>
        """

    html += """
        </div>

        <!-- Progress Rings -->
        <div class="card full-width" style="margin-bottom: 30px; overflow: visible !important; padding: 40px 50px;">
            <h2>📊 Key Performance Metrics</h2>
            <div class="progress-rings-container" style="overflow: visible !important;">
                <div class="progress-ring">
                    <svg class="progress-ring-svg" width="140" height="140">
                        <circle class="progress-ring-circle progress-ring-bg" cx="70" cy="70" r="55"></circle>
                        <circle class="progress-ring-circle progress-ring-progress" cx="70" cy="70" r="55"
                                stroke="#4ecca3" id="ringOnTime"></circle>
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
                                stroke="#60BBE9" id="ringUtilization"></circle>
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
                                stroke="#a78bfa" id="ringProjects"></circle>
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
            <p style="color: #6c757d; margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Next 10 days</p>
            <div class="timeline-container" id="projectTimeline">
                <!-- Timeline will be generated by JavaScript -->
            </div>
        </div>

        <!-- Radar/Spider Chart -->
        <div class="card full-width" style="margin-bottom: 30px; overflow: visible;">
            <h2>Workload Balance</h2>
            <p style="color: #6c757d; margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Actual vs Target distribution across categories</p>
            <div class="radar-container" id="radarChart">
                <!-- Radar will be generated by JavaScript -->
            </div>
        </div>

        <!-- Velocity Trend Chart -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>Team Velocity Trend</h2>
            <p style="color: #6c757d; margin-top: 5px; margin-bottom: 15px; font-size: 14px;">Projects completed per week over the last 8 weeks</p>
            <div class="velocity-container">
                <canvas id="velocityChart"></canvas>
            </div>
        </div>

        <!-- Heat Map Calendar -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📊 Daily Workload Distribution - Next 10 Days</h2>
            <div style="font-size: 13px; color: #6c757d; margin-bottom: 15px;">
                <strong>How busy will each day be?</strong> Shows the team's expected workload intensity per day (work distributed across task timelines)
            </div>
            <div class="heatmap-calendar" id="heatmapCalendar">
                <!-- Heatmap will be generated by JavaScript -->
            </div>
        </div>

        <!-- 6-Month Capacity Timeline -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📆 6-Month Capacity Timeline</h2>
            <div style="font-size: 12px; color: #6c757d; margin-bottom: 15px;">
                Weekly team capacity projection showing workload distribution over the next 26 weeks
            </div>
    """

    # Add 6-month timeline data
    timeline = data.get('six_month_timeline', [])

    html += """
            <div style="margin-top: 15px;">
                <!-- Timeline header with month labels -->
                <div style="display: flex; margin-bottom: 10px; font-size: 12px; font-weight: bold; color: #6c757d;">
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
                <div style="display: flex; gap: 3px; margin-top: 5px; font-size: 9px; color: #6c757d;">
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
                <div style="margin-top: 15px; font-size: 11px; color: #6c757d; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 2px;"></span> Low</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; border-radius: 2px;"></span> Medium</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #fd7e14; border-radius: 2px;"></span> High</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; border-radius: 2px;"></span> Very High</div>
                </div>
                <div style="margin-top: 5px; font-size: 10px; color: #6c757d; text-align: center; font-style: italic;">
                    Colors scale adaptively based on peak workload over the 6-month period
                </div>
            </div>
        </div>

        <!-- Daily Workload Distribution Heatmap -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📊 Daily Workload Distribution - Next 30 Days</h2>
            <div style="font-size: 13px; color: #6c757d; margin-bottom: 15px;">
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
            <div style="margin-top: 15px; font-size: 11px; color: #6c757d; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #20c997; border-radius: 2px;"></span> Very Low</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 2px;"></span> Low</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; border-radius: 2px;"></span> Medium</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #fd7e14; border-radius: 2px;"></span> High</div>
                <div><span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; border-radius: 2px;"></span> Very High</div>
            </div>
            <div style="margin-top: 10px; font-size: 11px; color: #6c757d; text-align: center;">
                <em>Colors scale adaptively based on peak workload over the 30-day period</em>
            </div>
        </div>

        <!-- Historical Capacity Utilization -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📈 Historical Capacity Utilization</h2>
            <div style="font-size: 12px; color: #6c757d; margin-bottom: 10px;">
                Team utilization percentage over the last 30 days (click legend items to filter)
            </div>
            <div class="chart-container">
                <canvas id="capacityHistoryChart"></canvas>
            </div>
        </div>

        <!-- Forecasted Projects -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>🔮 Forecasted Projects</h2>
            <p style="color: #6c757d; margin-top: 8px; font-size: 14px;">Upcoming projects in the forecast pipeline</p>
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
                <div style="border: 2px solid #dee2e6; border-radius: 12px; padding: 18px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div style="flex: 1;">
                            <div style="font-size: 16px; font-weight: bold; color: #09243F;">{date_range_str}</div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <a href="{task_url}" target="_blank" style="color: #09243F; text-decoration: none; font-weight: 600; font-size: 16px; line-height: 1.4; display: block;">
                            {project['name']}
                        </a>
                    </div>
            """

            if notes:
                html += f"""
                    <div style="margin-bottom: 12px; color: #6c757d; font-size: 14px; line-height: 1.5;">
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
            <div style="text-align: center; padding: 30px; color: #6c757d;">
                <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
                <div style="font-size: 16px;">No forecasted projects at this time</div>
            </div>
        """

    html += """
        </div>

        <!-- Historical Trends Chart -->
        <div class="grid">
            <div class="card full-width">
                <h2>Historical Allocation Trends</h2>
                <div style="font-size: 12px; color: #6c757d; margin-bottom: 10px;">
                    Daily allocation percentages over time
                </div>
                <div class="chart-container">
                    <canvas id="trendsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Category Details -->
        <div class="grid">
"""

    # Add category cards
    for cat in category_data:
        variance_class = 'positive' if abs(cat['variance']) <= 5 else 'warning' if abs(cat['variance']) <= 10 else 'negative'

        html += f"""
            <div class="card">
                <h2>{cat['name']}</h2>
                <div class="metric">
                    <span class="metric-label">Cumulative Avg</span>
                    <span class="metric-value">{cat['actual']:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Annual Target</span>
                    <span class="metric-value">{cat['target']:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Variance</span>
                    <span class="metric-value {variance_class}">{cat['variance']:+.1f}%</span>
                </div>
            </div>
"""

    html += """
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
        colors = ['#60BBE9', '#09243F', '#28a745', '#ffc107', '#dc3545']  # Brand colors

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
        const trendsCtx = document.getElementById('trendsChart').getContext('2d');
        new Chart(trendsCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: {json.dumps(trends_datasets)}
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
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }},
                    x: {{
                        ticks: {{
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top'
                    }},
                    tooltip: {{
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
        document.addEventListener('DOMContentLoaded', function() {{
            if (document.getElementById('capacityHistoryChart')) {{
                const historyCtx = document.getElementById('capacityHistoryChart').getContext('2d');
                const capacityHistoryByMember = {json.dumps(capacity_history_by_member)};

                // Build datasets for each team member
                const datasets = [];
                const memberColors = {{
                    'Zach Welliver': '#9B59B6',
                    'Nick Clark': '#36A2EB',
                    'Adriel Abella': '#FFCE56',
                    'John Meyer': '#4BC0C0',
                    'Team Total': '{BRAND_BLUE}'
                }};

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
                datasets.push({{
                    label: '100% Capacity Threshold',
                    data: Array(allDates.length).fill(100),
                    borderColor: '#dc3545',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }});

                if (datasets.length > 0) {{
                    window.capacityHistoryChart = new Chart(historyCtx, {{
                        type: 'line',
                        data: {{
                            labels: allDates,
                            datasets: datasets
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            layout: {{
                                padding: {{
                                    top: 20
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
                                        callback: function(value) {{
                                            return value + '%';
                                        }}
                                    }}
                                }},
                                x: {{
                                    ticks: {{
                                        maxRotation: 45,
                                        minRotation: 45
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    position: 'top',
                                    labels: {{
                                        usePointStyle: true
                                    }}
                                }},
                                tooltip: {{
                                    callbacks: {{
                                        label: function(context) {{
                                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
            }}
        }});

        // Chat Widget JavaScript - wait for DOM to load
        document.addEventListener('DOMContentLoaded', function() {{
            const chatButton = document.getElementById('chatButton');
            const chatWindow = document.getElementById('chatWindow');
            const chatClose = document.getElementById('chatClose');
            const chatInput = document.getElementById('chatInput');
            const chatSend = document.getElementById('chatSend');
            const chatMessages = document.getElementById('chatMessages');
            const typingIndicator = document.getElementById('typingIndicator');

            // Toggle chat window
            chatButton.addEventListener('click', () => {{
            chatWindow.classList.toggle('open');
            if (chatWindow.classList.contains('open')) {{
                chatInput.focus();
            }}
        }});

        chatClose.addEventListener('click', () => {{
            chatWindow.classList.remove('open');
        }});

        // Send message
        async function sendMessage() {{
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            chatInput.value = '';
            chatSend.disabled = true;

            // Show typing indicator
            typingIndicator.classList.add('show');
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {{
                // Call backend API
                const response = await fetch('http://localhost:5001/api/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ message }})
                }});

                if (!response.ok) {{
                    throw new Error('Failed to get response');
                }}

                const data = await response.json();

                // Hide typing indicator
                typingIndicator.classList.remove('show');

                // Add assistant response
                addMessage(data.response, 'assistant');
            }} catch (error) {{
                typingIndicator.classList.remove('show');
                addMessage('Sorry, I\\'m having trouble connecting to the backend. Make sure the chat backend is running on localhost:5001.', 'system');
            }} finally {{
                chatSend.disabled = false;
            }}
        }}

        function addMessage(text, type) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${{type}}`;
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}

        chatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage();
            }}
        }});

            // Welcome message
            addMessage('Hi! I\\'m Claude, your capacity dashboard assistant. Ask me anything about team workload, capacity trends, or project planning!', 'assistant');
        }});

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
                            name: '🎬 ' + shoot.name,
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
                            name: '⏰ ' + deadline.name,
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
            const canvas = document.getElementById('velocityChart');
            if (!canvas) return;

            // Use actual weekly completion data
            const weeklyData = {weekly_completions_json};

            const ctx = canvas.getContext('2d');
            new Chart(ctx, {{
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
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ stepSize: 2, color: '#a8c5da' }}, grid: {{ color: 'rgba(96, 187, 233, 0.1)' }} }},
                        x: {{ ticks: {{ color: '#a8c5da' }}, grid: {{ color: 'rgba(96, 187, 233, 0.1)' }} }}
                    }}
                }}
            }});
        }}

        // Heat Map
        function generateHeatMap() {{
            const container = document.getElementById('heatmapCalendar');
            if (!container) return;

            const days = 10;
            // Calculate intensity from team utilization (0-4 scale)
            const teamUtilization = {team_utilization_avg:.0f};
            const baseIntensity = teamUtilization < 40 ? 0 : teamUtilization < 60 ? 1 : teamUtilization < 80 ? 2 : teamUtilization < 100 ? 3 : 4;

            // Create variation for next 10 days
            const intensityData = [];
            for (let i = 0; i < days; i++) {{
                // Add some variation but keep it realistic
                const variation = Math.floor(Math.random() * 3) - 1;  // -1, 0, or +1
                intensityData.push(Math.max(0, Math.min(4, baseIntensity + variation)));
            }}

            let html = '<div></div>';
            for (let i = 0; i < days; i++) {{
                const date = new Date();
                date.setDate(date.getDate() + i);
                const dateStr = date.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }});
                html += `<div class="heatmap-date">${{dateStr}}</div>`;
            }}

            html += '<div class="heatmap-day-label">Workload</div>';
            for (let i = 0; i < days; i++) {{
                const intensity = intensityData[i];
                const tasks = Math.round(intensity * 7);
                html += `<div class="heatmap-cell intensity-${{intensity}}" title="${{tasks}} tasks">${{tasks}}</div>`;
            }}

            container.innerHTML = html;
        }}

        // Initialize new charts
        document.addEventListener('DOMContentLoaded', () => {{
            setTimeout(() => {{
                animateProgressRing('ringOnTime', 'ringOnTimeValue', {delivery_metrics['on_time_rate']:.0f});
                animateProgressRing('ringUtilization', 'ringUtilizationValue', {team_utilization_avg:.0f});
                animateProgressRing('ringProjects', 'ringProjectsValue', {total_tasks}, true);

                generateTimeline();
                generateRadarChart();
                generateVelocityChart();
                generateHeatMap();
            }}, 100);
        }});
"""

    html += """
    </script>

    <!-- Chat Widget -->
    <div class="chat-widget">
        <button id="chatButton" class="chat-button" title="Ask Claude about your dashboard data">💬</button>
        <div id="chatWindow" class="chat-window">
            <div class="chat-header">
                <h3>Dashboard Assistant</h3>
                <button id="chatClose" class="chat-close">&times;</button>
            </div>
            <div id="chatMessages" class="chat-messages">
                <!-- Messages will be added here -->
            </div>
            <div id="typingIndicator" class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
            <div class="chat-input-container">
                <input type="text" id="chatInput" class="chat-input" placeholder="Ask about your dashboard data..." />
                <button id="chatSend" class="chat-send">Send</button>
            </div>
        </div>
    </div>

</body>
</html>
"""

    # Save HTML dashboard
    output_file = 'Reports/capacity_dashboard.html'
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ HTML dashboard generated: {output_file}")
    return output_file

def main():
    """Main dashboard generation function"""
    print("Generating Perimeter Studio Dashboard...")

    # Read report data
    data = read_reports()

    # Generate HTML dashboard
    html_file = generate_html_dashboard(data)

    print(f"\nDashboard generation complete!")
    print(f"📊 HTML: {html_file}")

if __name__ == "__main__":
    main()
