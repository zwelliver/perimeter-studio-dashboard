"""
FastAPI main application entry point for Studio Dashboard
Railway deployment compatible
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import dashboard, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting Studio Dashboard in {settings.environment} mode")
    logger.info(f"Reports directory: {settings.reports_dir}")

    # Ensure reports directory exists
    os.makedirs(settings.reports_dir, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down Studio Dashboard")


# Create FastAPI app
app = FastAPI(
    title="Studio Dashboard",
    description="Perimeter Church Studio Operations Dashboard",
    version="2.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(health.router, prefix="/api", tags=["health"])

# Health endpoints are in health router

# Serve static files (frontend build)
frontend_dist = "studio-command-center/frontend/dist"
if os.path.exists(frontend_dist):
    logger.info(f"Mounting static files from: {frontend_dist}")
    app.mount("/static", StaticFiles(directory=f"{frontend_dist}/assets"), name="static")
else:
    logger.warning(f"Frontend dist directory not found: {frontend_dist}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Directory contents: {os.listdir('.')}")

# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the React frontend"""
    frontend_path = "studio-command-center/frontend/dist/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        logger.warning(f"Frontend index.html not found: {frontend_path}")
        return {"message": "Studio Dashboard API", "docs": "/docs", "frontend_missing": True}

# Catch-all route for frontend routing (SPA)
@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """Handle frontend routing for single-page application"""
    # Don't intercept API routes
    if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
        return {"error": "Not found"}, 404

    frontend_path = "studio-command-center/frontend/dist/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {"error": "Frontend not built"}, 404


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )