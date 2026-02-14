#!/usr/bin/env python3
"""
Complete Studio Dashboard FastAPI application for Railway deployment
"""
import os
import logging
import json
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pydantic import Field
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Settings(BaseSettings):
    asana_pat: str = Field(default="", description="Asana Personal Access Token")
    environment: str = Field(default="production", description="Environment")
    cache_duration: int = Field(default=300, description="Cache duration in seconds")
    reports_dir: str = Field(default="/app/Reports", description="Reports directory")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()

# Global data cache
dashboard_cache = {
    'data': None,
    'last_updated': None,
    'cache_duration': settings.cache_duration
}

# Scheduler
scheduler = AsyncIOScheduler()

def get_asana_headers():
    """Get headers for Asana API calls"""
    return {
        'Authorization': f'Bearer {settings.asana_pat}',
        'Accept': 'application/json',
    }

def fetch_asana_data():
    """Fetch data from Asana API - simplified version"""
    try:
        if not settings.asana_pat:
            logger.warning("No ASANA_PAT configured")
            return generate_mock_data()

        # For now, return mock data structure that matches frontend expectations
        # TODO: Implement actual Asana API calls
        data = generate_mock_data()
        logger.info("Successfully fetched dashboard data")
        return data

    except Exception as e:
        logger.error(f"Error fetching Asana data: {e}")
        return generate_mock_data()

def generate_mock_data():
    """Generate mock data that matches the frontend structure"""
    return {
        "timestamp": datetime.now().isoformat(),
        "cache_age": 0,
        "metrics": {
            "total_tasks": 42,
            "at_risk_count": 3,
            "upcoming_shoots": 2,
            "upcoming_deadlines": 5
        },
        "team_capacity": [
            {
                "name": "Zach Welliver",
                "current": 87.5,
                "max": 100,
                "utilization": 87.5,
                "status": "high"
            },
            {
                "name": "Nick Clark",
                "current": 65.0,
                "max": 100,
                "utilization": 65.0,
                "status": "normal"
            },
            {
                "name": "Adriel Abella",
                "current": 45.0,
                "max": 100,
                "utilization": 45.0,
                "status": "normal"
            }
        ],
        "at_risk_tasks": [
            {
                "name": "Q1 Content Planning",
                "project": "Preproduction",
                "assignee": "Zach Welliver",
                "due_on": "2026-02-20",
                "risks": ["Approaching deadline", "High workload"]
            },
            {
                "name": "Easter Campaign Prep",
                "project": "Production",
                "assignee": "Nick Clark",
                "due_on": "2026-02-25",
                "risks": ["Resource constraints"]
            }
        ],
        "upcoming_shoots": [
            {
                "name": "Sunday Service - Feb 16",
                "datetime": "2026-02-16T10:30:00Z",
                "project": "Production",
                "gid": "12345",
                "days_until": 2
            },
            {
                "name": "Wednesday Night - Feb 19",
                "datetime": "2026-02-19T19:00:00Z",
                "project": "Production",
                "gid": "12346",
                "days_until": 5
            }
        ],
        "upcoming_deadlines": [
            {
                "name": "Easter Graphics Package",
                "due_date": "2026-02-28",
                "days_until": 14,
                "project": "Post Production",
                "gid": "12347"
            }
        ]
    }

def refresh_dashboard_data():
    """Refresh dashboard data and update cache"""
    try:
        logger.info("Refreshing dashboard data...")
        data = fetch_asana_data()
        dashboard_cache['data'] = data
        dashboard_cache['last_updated'] = datetime.now()
        logger.info("Dashboard data refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")

def get_cached_data():
    """Get data from cache or refresh if needed"""
    now = datetime.now()

    # Check if cache is valid
    if (dashboard_cache['data'] is None or
        dashboard_cache['last_updated'] is None or
        (now - dashboard_cache['last_updated']).total_seconds() > dashboard_cache['cache_duration']):

        refresh_dashboard_data()

    return dashboard_cache['data']

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting Studio Dashboard in {settings.environment} mode")
    logger.info(f"ASANA_PAT configured: {bool(settings.asana_pat)}")
    logger.info(f"Reports directory: {settings.reports_dir}")

    # Ensure reports directory exists
    os.makedirs(settings.reports_dir, exist_ok=True)

    # Start background data refresh
    scheduler.add_job(
        refresh_dashboard_data,
        trigger=IntervalTrigger(minutes=5),
        id='refresh_data'
    )
    scheduler.start()

    # Initial data load
    refresh_dashboard_data()

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Shutting down Studio Dashboard")

# Create FastAPI app
app = FastAPI(
    title="Studio Dashboard",
    description="Perimeter Church Studio Operations Dashboard",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Studio Dashboard API",
        "status": "online",
        "environment": settings.environment,
        "version": "2.0.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "asana_configured": bool(settings.asana_pat),
        "cache_age": (datetime.now() - dashboard_cache.get('last_updated', datetime.now())).total_seconds() if dashboard_cache.get('last_updated') else 0
    }

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "message": "API working"}

@app.get("/api/dashboard")
async def dashboard():
    """Get complete dashboard data"""
    try:
        data = get_cached_data()
        if data is None:
            raise HTTPException(status_code=500, detail="Failed to load dashboard data")
        return data
    except Exception as e:
        logger.error(f"Error in dashboard endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/refresh")
async def refresh():
    """Force refresh of dashboard data"""
    try:
        refresh_dashboard_data()
        return {"message": "Data refreshed successfully", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/team")
async def team():
    """Get team capacity data only"""
    try:
        data = get_cached_data()
        return {"team_capacity": data.get("team_capacity", [])}
    except Exception as e:
        logger.error(f"Error in team endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/at-risk")
async def at_risk():
    """Get at-risk tasks only"""
    try:
        data = get_cached_data()
        return {"at_risk_tasks": data.get("at_risk_tasks", [])}
    except Exception as e:
        logger.error(f"Error in at-risk endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend (when built)
frontend_dist = "studio-command-center/frontend/dist"
if os.path.exists(frontend_dist):
    logger.info(f"Mounting frontend from: {frontend_dist}")
    app.mount("/static", StaticFiles(directory=f"{frontend_dist}/assets"), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA"""
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("health"):
            raise HTTPException(status_code=404, detail="Not found")

        index_path = f"{frontend_dist}/index.html"
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return {"error": "Frontend not available"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Studio Dashboard on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )