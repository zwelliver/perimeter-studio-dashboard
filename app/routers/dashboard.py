"""
Dashboard API endpoints for Studio Command Center.
Maintains compatibility with existing Flask API.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
import httpx
import logging

from app.config import settings
from app.services.reports import get_fresh_data, clear_cache, get_cache_age

logger = logging.getLogger(__name__)
router = APIRouter()

TASK_PROGRESS_FIELD_GID = "1209598240843051"
_filmed_option_gid: str | None = None


async def _get_filmed_option_gid() -> str:
    """Look up the 'Filmed' enum option GID from the Task Progress custom field. Cached after first call."""
    global _filmed_option_gid
    if _filmed_option_gid:
        return _filmed_option_gid

    url = f"https://app.asana.com/api/1.0/custom_fields/{TASK_PROGRESS_FIELD_GID}"
    headers = {"Authorization": f"Bearer {settings.asana_pat_scorer}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch custom field from Asana")
        data = resp.json().get("data", {})

    for option in data.get("enum_options", []):
        if option.get("name", "").strip().lower() == "filmed":
            _filmed_option_gid = option["gid"]
            return _filmed_option_gid

    raise HTTPException(status_code=500, detail="'Filmed' option not found in Task Progress field")


@router.post("/api/tasks/{task_gid}/mark-filmed")
async def mark_filmed(task_gid: str):
    """Mark a task's Task Progress custom field as 'Filmed' in Asana."""
    filmed_gid = await _get_filmed_option_gid()

    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    headers = {"Authorization": f"Bearer {settings.asana_pat_scorer}"}
    payload = {
        "data": {
            "custom_fields": {
                TASK_PROGRESS_FIELD_GID: filmed_gid,
            }
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.put(url, headers=headers, json=payload)

    if resp.status_code != 200:
        logger.error("Failed to mark task %s as filmed: %s", task_gid, resp.text)
        raise HTTPException(status_code=502, detail="Failed to update task in Asana")

    return {"status": "ok", "task_gid": task_gid}


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