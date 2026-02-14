"""
Health check endpoints for Studio Command Center.
"""

from datetime import datetime
from fastapi import APIRouter

from app.config import settings
# Temporarily use simple mock data to debug deployment
# from app.services.reports import get_cache_age
from app.services.reports_simple import get_cache_age

router = APIRouter()


@router.get("/api/status")
async def status():
    """Health check endpoint - compatible with Flask version."""
    return {
        'status': 'ok',
        'service': 'Studio Command Center API',
        'timestamp': datetime.now().isoformat(),
        'cache_age': get_cache_age()
    }


@router.get("/api/health")
async def health_check():
    """Additional health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "version": settings.app_version
    }