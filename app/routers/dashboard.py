"""
Dashboard API endpoints for Studio Command Center.
Maintains compatibility with existing Flask API.
"""

from datetime import datetime
from fastapi import APIRouter
import logging

from app.services.reports import get_fresh_data, clear_cache, get_cache_age

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/refresh")
async def refresh():
    """Force refresh data from Asana - compatible with Flask version."""
    clear_cache()
    data = get_fresh_data(force_refresh=True)

    return {
        'status': 'refreshed',
        'timestamp': datetime.now().isoformat()
    }


@router.get("/api/dashboard")
async def dashboard():
    """Get all dashboard data - compatible with Flask version."""
    data = get_fresh_data()

    # Prepare response with same structure as Flask version
    response = {
        'timestamp': datetime.now().isoformat(),
        'cache_age': get_cache_age() or 0,

        # Summary metrics
        'metrics': {
            'total_tasks': data.get('active_task_count', 0),
            'at_risk_count': len(data.get('at_risk_tasks', [])),
            'upcoming_shoots': len(data.get('upcoming_shoots', [])),
            'upcoming_deadlines': len(data.get('upcoming_deadlines', [])),
        },

        # Team capacity
        'team_capacity': data.get('team_capacity', []),

        # At-risk tasks
        'at_risk_tasks': data.get('at_risk_tasks', [])[:20],  # Limit to 20

        # Upcoming shoots
        'upcoming_shoots': [
            {
                'name': s['name'],
                'datetime': s['datetime'].isoformat() if hasattr(s['datetime'], 'isoformat') else str(s['datetime']),
                'project': s.get('project', 'Unknown'),
                'gid': s.get('gid'),
                'start_on': s['start_on'].isoformat() if s.get('start_on') and hasattr(s['start_on'], 'isoformat') else None,
                'due_on': s['due_on'].isoformat() if s.get('due_on') and hasattr(s['due_on'], 'isoformat') else None,
            }
            for s in data.get('upcoming_shoots', [])[:10]
        ],

        # Upcoming deadlines
        'upcoming_deadlines': [
            {
                'name': d['name'],
                'due_date': d['due_date'].isoformat() if hasattr(d['due_date'], 'isoformat') else str(d['due_date']),
                'days_until': d.get('days_until', 0),
                'project': d.get('project', 'Unknown'),
                'gid': d.get('gid'),
                'start_on': d['start_on'].isoformat() if d.get('start_on') and hasattr(d['start_on'], 'isoformat') else None,
            }
            for d in data.get('upcoming_deadlines', [])[:10]
        ],

        # Category data
        'categories': data.get('category_data', []),

        # Delivery metrics
        'delivery_metrics': data.get('delivery_metrics', {}),

        # External projects
        'external_projects': data.get('external_projects', []),
    }

    return response


@router.get("/api/team")
async def team():
    """Get team capacity data - compatible with Flask version."""
    data = get_fresh_data()

    team_data = []
    for member in data.get('team_capacity', []):
        utilization = (member['current'] / member['max'] * 100) if member['max'] > 0 else 0
        team_data.append({
            'name': member['name'],
            'current': member['current'],
            'max': member['max'],
            'utilization': round(utilization, 1),
            'status': 'overloaded' if utilization > 100 else 'high' if utilization > 80 else 'normal'
        })

    return {
        'timestamp': datetime.now().isoformat(),
        'team': team_data
    }


@router.get("/api/at-risk")
async def at_risk():
    """Get at-risk tasks - compatible with Flask version."""
    data = get_fresh_data()

    tasks = []
    for task in data.get('at_risk_tasks', [])[:20]:
        tasks.append({
            'name': task['name'],
            'project': task.get('project', 'Unknown'),
            'assignee': task.get('assignee', 'Unassigned'),
            'videographer': task.get('videographer'),
            'due_on': task.get('due_on'),
            'risks': task.get('risks', [])
        })

    return {
        'timestamp': datetime.now().isoformat(),
        'count': len(tasks),
        'tasks': tasks
    }