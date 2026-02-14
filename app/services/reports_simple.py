"""
Simple reports service with mock data for testing Railway deployment.
Use this temporarily to isolate deployment issues from Asana integration.
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

# Mock data cache
_cache = {
    'data': None,
    'last_updated': None,
}


def get_mock_data() -> Dict:
    """Return mock data for testing."""
    return {
        'active_task_count': 42,
        'team_capacity': [
            {'name': 'John Doe', 'current': 8, 'max': 10},
            {'name': 'Jane Smith', 'current': 12, 'max': 10},
            {'name': 'Bob Johnson', 'current': 6, 'max': 10},
        ],
        'at_risk_tasks': [
            {
                'name': 'Sample Task 1',
                'project': 'Test Project',
                'assignee': 'John Doe',
                'due_on': '2026-02-20',
                'risks': ['Overdue', 'High Priority']
            },
            {
                'name': 'Sample Task 2',
                'project': 'Another Project',
                'assignee': 'Jane Smith',
                'due_on': '2026-02-18',
                'risks': ['No progress']
            }
        ],
        'upcoming_shoots': [
            {
                'name': 'Weekly Service Shoot',
                'datetime': datetime(2026, 2, 16, 9, 0),
                'project': 'Weekly Services',
                'start_on': datetime(2026, 2, 16),
                'due_on': datetime(2026, 2, 17)
            }
        ],
        'upcoming_deadlines': [
            {
                'name': 'Video Edit Deadline',
                'due_date': datetime(2026, 2, 20, 17, 0),
                'days_until': 6,
                'project': 'Special Event',
                'start_on': datetime(2026, 2, 15)
            }
        ],
        'category_data': [],
        'delivery_metrics': {},
        'external_projects': []
    }


def get_fresh_data(force_refresh: bool = False) -> Dict:
    """
    Get data - returns mock data for testing deployment.

    Args:
        force_refresh: Ignored in mock version

    Returns:
        Dict containing mock dashboard data
    """
    logger.info("Returning mock data for testing")

    now = datetime.now()
    _cache['data'] = get_mock_data()
    _cache['last_updated'] = now

    return _cache['data']


def get_cache_age() -> float:
    """Get the age of cached data in seconds."""
    if _cache['last_updated']:
        return (datetime.now() - _cache['last_updated']).total_seconds()
    return 0


def clear_cache() -> None:
    """Clear the cached data."""
    _cache['data'] = None
    _cache['last_updated'] = None
    logger.info("Mock cache cleared")