"""
Studio Command Center - FastAPI Backend
Serves real-time Asana data for the interactive dashboard
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, dashboard
from app.services.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Static files directory (React frontend build)
STATIC_DIR = Path(__file__).parent.parent / "studio-command-center" / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle - startup and shutdown."""
    logger.info(f"Studio Command Center backend starting (environment={settings.environment})")
    logger.info(f"Static files directory: {STATIC_DIR}")

    # Start background scheduler
    start_scheduler()
    logger.info("Background scheduler started")

    yield

    # Cleanup on shutdown
    stop_scheduler()
    logger.info("Studio Command Center backend shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Backend API for Studio Command Center - real-time Asana dashboard",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(dashboard.router)

# Debug static directory path
logger.info(f"Looking for static files at: {STATIC_DIR}")
logger.info(f"Static directory exists: {STATIC_DIR.exists()}")

# List all possible frontend locations for debugging
possible_paths = [
    STATIC_DIR,
    Path(__file__).parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "build",
    Path(__file__).parent / "static"
]

for path in possible_paths:
    logger.info(f"Checking path {path}: exists={path.exists()}")
    if path.exists():
        logger.info(f"Contents of {path}: {list(path.iterdir())}")

# Mount static files if the directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Mounted static files from: {STATIC_DIR}")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    Catch-all route to serve index.html for the SPA.
    This handles client-side routing for React.
    """
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})

    # Try to serve static file first
    if STATIC_DIR.exists():
        static_file = STATIC_DIR / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))

        # Fall back to index.html for SPA routing
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    # No static files available
    return JSONResponse(
        status_code=200,
        content={
            "message": f"{settings.app_name} API is running",
            "version": settings.app_version,
            "environment": settings.environment,
            "note": "Frontend not yet deployed or static files not found"
        },
    )