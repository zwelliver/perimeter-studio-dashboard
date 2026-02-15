"""
Background task scheduler for Studio Command Center.
Runs dashboard generation tasks on a scheduled interval.
"""

import logging
import sys
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

# Add the parent directory to Python path to import generate_dashboard
sys.path.append(str(Path(__file__).parent.parent.parent))
import generate_dashboard

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_dashboard_data():
    """Background job to regenerate dashboard HTML."""
    try:
        logger.info("Running scheduled dashboard regeneration...")
        generate_dashboard.main()
        logger.info("Dashboard HTML regeneration complete")
    except Exception as e:
        logger.error(f"Scheduled dashboard regeneration failed: {e}")


def start_scheduler():
    """Configure and start the APScheduler."""
    # Dashboard HTML regeneration every 5 minutes
    scheduler.add_job(
        refresh_dashboard_data,
        trigger=IntervalTrigger(minutes=settings.background_refresh_interval),
        id="dashboard_refresh",
        name="Dashboard HTML Regeneration",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started: dashboard HTML regeneration every {settings.background_refresh_interval} minutes"
    )


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")