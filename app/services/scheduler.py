"""
Background task scheduler for Studio Command Center.
Runs data refresh tasks on a scheduled interval.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.reports import get_fresh_data

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_dashboard_data():
    """Background job to refresh dashboard data."""
    try:
        logger.info("Running scheduled dashboard data refresh...")
        data = get_fresh_data(force_refresh=True)
        logger.info(f"Dashboard data refresh complete. Active tasks: {data.get('active_task_count', 0)}")
    except Exception as e:
        logger.error(f"Scheduled dashboard refresh failed: {e}")


def start_scheduler():
    """Configure and start the APScheduler."""
    # Dashboard data refresh every 5 minutes
    scheduler.add_job(
        refresh_dashboard_data,
        trigger=IntervalTrigger(minutes=settings.background_refresh_interval),
        id="dashboard_refresh",
        name="Dashboard Data Refresh",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started: dashboard refresh every {settings.background_refresh_interval} minutes"
    )


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")