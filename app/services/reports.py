"""
Report processing service with caching functionality.
Wraps the existing generate_dashboard.py functions.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Optional
import logging

# Add parent directory to path to import from StudioProcesses
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the existing data collection functions
from generate_dashboard import read_reports

from app.config import settings

logger = logging.getLogger(__name__)

# Global cache instance
_cache = {
    'data': None,
    'last_updated': None,
}


def get_fresh_data(force_refresh: bool = False) -> Dict:
    """
    Get fresh data from Asana or return cached data if recent.

    Args:
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        Dict containing dashboard data
    """
    now = datetime.now()

    # Return cached data if it's recent and not forcing refresh
    if not force_refresh and _cache['data'] and _cache['last_updated']:
        elapsed = (now - _cache['last_updated']).total_seconds()
        if elapsed < settings.cache_duration:
            logger.debug(f"Returning cached data (age: {elapsed:.1f}s)")
            return _cache['data']

    # Fetch fresh data
    logger.info(f"Fetching fresh data from Asana at {now.strftime('%H:%M:%S')}")

    try:
        data = read_reports()

        # Update cache
        _cache['data'] = data
        _cache['last_updated'] = now

        logger.info("Data fetched and cached successfully")
        return data

    except Exception as e:
        logger.error(f"Failed to fetch fresh data: {e}")
        # Return cached data if available, even if stale
        if _cache['data']:
            logger.warning("Returning stale cached data due to fetch error")
            return _cache['data']
        # Re-raise if no cached data available
        raise


def get_cache_age() -> Optional[float]:
    """Get the age of cached data in seconds."""
    if _cache['last_updated']:
        return (datetime.now() - _cache['last_updated']).total_seconds()
    return None


def clear_cache() -> None:
    """Clear the cached data."""
    _cache['data'] = None
    _cache['last_updated'] = None
    logger.info("Cache cleared")


def serialize_datetime(obj):
    """Convert datetime objects to ISO strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj