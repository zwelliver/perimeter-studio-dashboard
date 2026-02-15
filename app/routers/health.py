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


@router.get("/api/debug/files")
async def debug_files():
    """Debug endpoint to check file system structure."""
    import os
    from pathlib import Path

    current_dir = Path.cwd()

    def list_dir(path_str, max_depth=2, current_depth=0):
        """Recursively list directory contents."""
        if current_depth >= max_depth:
            return "Max depth reached"

        try:
            path = Path(path_str)
            if not path.exists():
                return f"Path does not exist: {path}"

            if path.is_file():
                return f"File: {path.name}"

            items = {}
            for item in path.iterdir():
                if item.is_file():
                    items[item.name] = f"File ({item.stat().st_size} bytes)"
                else:
                    items[item.name] = list_dir(str(item), max_depth, current_depth + 1)
            return items
        except Exception as e:
            return f"Error: {str(e)}"

    return {
        "current_working_directory": str(current_dir),
        "app_directory": list_dir("app"),
        "root_directory": list_dir("."),
        "studio_command_center": list_dir("studio-command-center") if Path("studio-command-center").exists() else "Not found",
        "frontend_dist": list_dir("studio-command-center/frontend/dist") if Path("studio-command-center/frontend/dist").exists() else "Not found"
    }