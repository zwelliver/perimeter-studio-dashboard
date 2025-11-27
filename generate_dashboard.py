"""
Perimeter Studio Capacity Dashboard Generator
Generates interactive HTML dashboard
"""

import pandas as pd
import os
import json
import math
from datetime import datetime, timedelta

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
        'team_capacity': []
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

    # Fetch active tasks from Asana to calculate team capacity accurately
    team_capacity_config = {
        'Zach Welliver': {'max': 50},
        'Nick Clark': {'max': 100},
        'Adriel Abella': {'max': 120},
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

        # Project GIDs
        project_gids = {
            'Preproduction': '1208336083003480',
            'Production': '1209597979075357',
            'Post Production': '1209581743268502',
            'Forecast': '1212059678473189'
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
                        'task_progress': task_progress
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
            at_risk.append({
                'name': task['name'],
                'project': task['project'],
                'assignee': assignee,
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
        'on_time_rate': 0,
        'avg_capacity_variance': 0,
        'projects_delayed_capacity': 0,
        'avg_days_variance': 0
    }

    if data['delivery_log'] is not None:
        df = data['delivery_log']
        delivery_metrics['total_completed'] = len(df)

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
            background-color: {BRAND_OFF_WHITE};
            color: {BRAND_NAVY};
            padding: 20px;
        }}

        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border-left: 5px solid {BRAND_BLUE};
        }}

        .header h1 {{
            color: {BRAND_NAVY};
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .header .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}

        .header .timestamp {{
            color: {BRAND_BLUE};
            font-size: 13px;
            margin-top: 5px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .card h2 {{
            color: {BRAND_NAVY};
            font-size: 18px;
            margin-bottom: 15px;
            font-weight: 600;
            border-bottom: 2px solid {BRAND_BLUE};
            padding-bottom: 10px;
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e9ecef;
        }}

        .metric:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            font-size: 14px;
            color: #6c757d;
        }}

        .metric-value {{
            font-size: 24px;
            font-weight: 600;
            color: {BRAND_NAVY};
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
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
            margin-top: 8px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {BRAND_BLUE}, #4a9fd8);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}

        .progress-fill.over-capacity {{
            background: linear-gradient(90deg, #dc3545, #c82333);
        }}

        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
        }}

        .alert.danger {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}

        .alert.success {{
            background: #d4edda;
            border-left-color: #28a745;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 15px;
        }}

        .team-member {{
            margin-bottom: 20px;
        }}

        .team-member-name {{
            font-size: 14px;
            font-weight: 600;
            color: {BRAND_NAVY};
            margin-bottom: 5px;
        }}

        .team-member-capacity {{
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
        }}

        .full-width {{
            grid-column: 1 / -1;
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
            background: {BRAND_BLUE};
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}

        .chat-button:hover {{
            background: {BRAND_NAVY};
            transform: scale(1.05);
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
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            flex-direction: column;
            overflow: hidden;
        }}

        .chat-window.open {{
            display: flex;
        }}

        .chat-header {{
            background: {BRAND_NAVY};
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
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
            border-radius: 12px;
            max-width: 80%;
            line-height: 1.4;
        }}

        .chat-message.user {{
            background: {BRAND_BLUE};
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}

        .chat-message.assistant {{
            background: white;
            color: {BRAND_NAVY};
            margin-right: auto;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .chat-message.system {{
            background: #ffe69c;
            color: #856404;
            margin: 0 auto;
            text-align: center;
            font-size: 13px;
        }}

        .chat-input-container {{
            padding: 15px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 10px;
        }}

        .chat-input {{
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
        }}

        .chat-input:focus {{
            outline: none;
            border-color: {BRAND_BLUE};
        }}

        .chat-send {{
            padding: 10px 20px;
            background: {BRAND_BLUE};
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }}

        .chat-send:hover {{
            background: {BRAND_NAVY};
        }}

        .chat-send:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}

        .typing-indicator {{
            display: none;
            padding: 10px 16px;
            background: white;
            border-radius: 12px;
            max-width: 60px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .typing-indicator.show {{
            display: block;
        }}

        .typing-indicator span {{
            height: 8px;
            width: 8px;
            background: {BRAND_BLUE};
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }}

        .typing-indicator span:nth-child(2) {{
            animation-delay: 0.2s;
        }}

        .typing-indicator span:nth-child(3) {{
            animation-delay: 0.4s;
        }}

        @keyframes typing {{
            0%, 60%, 100% {{
                opacity: 0.3;
            }}
            30% {{
                opacity: 1;
            }}
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
            <!-- Quick Stats -->
            <div class="card">
                <h2>Quick Stats</h2>
                <div class="metric">
                    <span class="metric-label">Active Tasks</span>
                    <span class="metric-value">{total_tasks}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Completed (30 days)</span>
                    <span class="metric-value">{delivery_metrics['total_completed']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Days Variance</span>
                    <span class="metric-value {'positive' if delivery_metrics['avg_days_variance'] <= 0 else 'warning' if delivery_metrics['avg_days_variance'] <= 3 else 'negative'}">{delivery_metrics['avg_days_variance']:+.1f}</span>
                </div>
            </div>

            <!-- Delivery Performance -->
            <div class="card">
                <h2>Delivery Performance</h2>
                <div class="metric">
                    <span class="metric-label">On-Time Completion Rate</span>
                    <span class="metric-value {'positive' if delivery_metrics['on_time_rate'] >= 80 else 'warning' if delivery_metrics['on_time_rate'] >= 60 else 'negative'}">{delivery_metrics['on_time_rate']:.0f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Average Capacity Variance</span>
                    <span class="metric-value {'positive' if not math.isnan(delivery_metrics['avg_capacity_variance']) and delivery_metrics['avg_capacity_variance'] <= 10 else 'warning' if not math.isnan(delivery_metrics['avg_capacity_variance']) and delivery_metrics['avg_capacity_variance'] <= 20 else 'negative' if not math.isnan(delivery_metrics['avg_capacity_variance']) else ''}">{'N/A' if delivery_metrics['avg_capacity_variance'] == 0 or math.isnan(delivery_metrics['avg_capacity_variance']) else f"{delivery_metrics['avg_capacity_variance']:+.0f}%"}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Projects Completed (30d)</span>
                    <span class="metric-value">{delivery_metrics['total_completed']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Delayed Due to Capacity</span>
                    <span class="metric-value {'positive' if delivery_metrics['projects_delayed_capacity'] == 0 else 'negative'}">{delivery_metrics['projects_delayed_capacity']}</span>
                </div>
            </div>

            <!-- Team Capacity -->
            <div class="card">
                <h2>Team Capacity</h2>
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
            html += f"""
                <div style="border-left: 4px solid #dc3545; padding: 10px; margin-bottom: 10px; background: {BRAND_OFF_WHITE};">
                    <div style="font-weight: bold; color: {BRAND_NAVY};">{task['name']}</div>
                    <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                        {task['project']} | {task['assignee']} | Due: {task['due_on']}
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

        <!-- Upcoming Workload Forecast -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📅 Upcoming Workload Forecast</h2>
            <div class="grid" style="grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px;">
    """

    # Add workload forecast data
    workload = data.get('workload_forecast', {})
    for period_key in ['7_days', '14_days', '30_days']:
        period_data = workload.get(period_key, {})
        period_label = period_key.replace('_', ' ').title()
        tasks_count = period_data.get('tasks', 0)
        utilization = period_data.get('utilization', 0)
        status = period_data.get('status', 'good')
        relative_note = period_data.get('relative_note')

        # Status color
        if status == 'over':
            status_color = '#dc3545'
            status_icon = '⚠️'
        elif status == 'busy':
            status_color = '#ffc107'
            status_icon = '⚡'
        else:
            status_color = '#28a745'
            status_icon = '✅'

        # Build relative note HTML if present
        relative_note_html = ""
        if relative_note:
            relative_note_html = f"""
                    <div style="font-size: 11px; color: #6c757d; margin-top: 8px; padding-top: 8px; border-top: 1px solid #dee2e6; font-style: italic;">
                        📊 {relative_note}
                    </div>"""

        html += f"""
                <div style="border: 2px solid {status_color}; border-radius: 8px; padding: 15px; background: {BRAND_OFF_WHITE};">
                    <div style="font-size: 14px; color: #6c757d; margin-bottom: 5px;">{period_label}</div>
                    <div style="font-size: 24px; font-weight: bold; color: {BRAND_NAVY}; margin-bottom: 10px;">
                        {tasks_count} tasks
                    </div>
                    <div style="font-size: 18px; color: {status_color}; font-weight: bold; margin-bottom: 5px;">
                        {status_icon} {utilization:.0f}% capacity
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">
                        {status.replace('_', ' ').title() if status != 'over' else 'Over-allocated'}
                    </div>{relative_note_html}
                </div>
        """

    html += """
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

        <!-- Capacity Utilization Heatmap -->
        <div class="card full-width" style="margin-bottom: 30px;">
            <h2>📊 Capacity Utilization - Next 30 Days</h2>
            <div style="margin-top: 15px; display: grid; grid-template-columns: repeat(10, 1fr); gap: 5px;">
    """

    heatmap = data.get('capacity_heatmap', [])
    for day_data in heatmap:
        date_str = day_data.get('date', '')  # Full date like "2025-11-26"
        day_abbr = day_data.get('day', '')  # Day abbreviation like "Wed"
        utilization = day_data.get('utilization', 0)
        status = day_data.get('status', 'low')

        # Format date for display (show month/day)
        try:
            from datetime import datetime
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

    html += """
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

        <!-- Category Allocation Chart -->
        <div class="grid">
            <div class="card full-width">
                <h2>Category Allocation: Cumulative Average vs Target</h2>
                <div style="font-size: 12px; color: #6c757d; margin-bottom: 10px;">
                    Cumulative average allocation across tracking period: {tracking_period}
                </div>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
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
    actual_values = [cat['actual'] for cat in category_data]
    target_values = [cat['target'] for cat in category_data]

    html += f"""
        // Category Chart
        const ctx = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(category_names)},
                datasets: [
                    {{
                        label: 'Actual %',
                        data: {json.dumps(actual_values)},
                        backgroundColor: '{BRAND_BLUE}',
                        borderColor: '{BRAND_NAVY}',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Target %',
                        data: {json.dumps(target_values)},
                        backgroundColor: 'rgba(9, 36, 63, 0.3)',
                        borderColor: '{BRAND_NAVY}',
                        borderWidth: 2,
                        borderDash: [5, 5]
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 50,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
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
