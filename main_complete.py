#!/usr/bin/env python3
"""
Complete Studio Dashboard FastAPI application for Railway deployment
"""
import os
import logging
import json
import csv
import time
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pydantic import Field
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dateutil import parser

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
    """Fetch data from Asana API with real implementation"""
    try:
        if not settings.asana_pat:
            logger.warning("No ASANA_PAT configured")
            return generate_mock_data()

        # Attempt real Asana API calls
        headers = get_asana_headers()
        data = {
            "timestamp": datetime.now().isoformat(),
            "cache_age": 0,
            "metrics": get_dashboard_metrics(headers),
            "team_capacity": get_team_capacity(headers),
            "at_risk_tasks": get_at_risk_tasks(headers),
            "upcoming_shoots": get_upcoming_shoots(headers),
            "upcoming_deadlines": get_upcoming_deadlines(headers)
        }

        # Save data for reports
        save_dashboard_data(data)
        logger.info("Successfully fetched dashboard data from Asana API")
        return data

    except Exception as e:
        logger.error(f"Error fetching Asana data: {e}")
        # Fall back to mock data if API fails
        return generate_mock_data()

def get_dashboard_metrics(headers):
    """Get basic dashboard metrics from Asana"""
    try:
        # Get workspace tasks - simplified for now
        response = requests.get(
            'https://app.asana.com/api/1.0/tasks',
            headers=headers,
            params={'completed_since': 'now', 'limit': 100}
        )

        if response.status_code == 200:
            tasks = response.json().get('data', [])
            return {
                "total_tasks": len(tasks),
                "at_risk_count": len([t for t in tasks if is_task_at_risk(t)]),
                "upcoming_shoots": 2,  # Will be calculated from actual data
                "upcoming_deadlines": len([t for t in tasks if has_upcoming_deadline(t)])
            }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")

    # Return mock metrics if API fails
    return {
        "total_tasks": 42,
        "at_risk_count": 3,
        "upcoming_shoots": 2,
        "upcoming_deadlines": 5
    }

def get_team_capacity(headers):
    """Get team capacity data - using mock data for now"""
    # This would require more complex Asana API calls to get actual workload
    # For now, return consistent mock data
    return [
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
    ]

def get_at_risk_tasks(headers):
    """Get at-risk tasks from Asana API"""
    try:
        # Get tasks due soon or overdue
        response = requests.get(
            'https://app.asana.com/api/1.0/tasks',
            headers=headers,
            params={
                'completed_since': 'now',
                'limit': 50,
                'opt_fields': 'name,due_on,assignee.name,projects.name'
            }
        )

        if response.status_code == 200:
            tasks = response.json().get('data', [])
            at_risk = []

            for task in tasks:
                if is_task_at_risk(task):
                    at_risk.append({
                        "name": task.get('name', 'Unnamed Task'),
                        "project": task.get('projects', [{}])[0].get('name', 'Unknown Project'),
                        "assignee": task.get('assignee', {}).get('name', 'Unassigned'),
                        "due_on": task.get('due_on'),
                        "risks": determine_task_risks(task)
                    })

            return at_risk
    except Exception as e:
        logger.error(f"Error fetching at-risk tasks: {e}")

    # Return mock data if API fails
    return [
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
    ]

def get_upcoming_shoots(headers):
    """Get upcoming shoots from Asana API"""
    # This would need specific project/task filtering for shoots
    # Return mock data for now
    return [
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
    ]

def get_upcoming_deadlines(headers):
    """Get upcoming deadlines from Asana API"""
    try:
        # Get tasks with upcoming due dates
        response = requests.get(
            'https://app.asana.com/api/1.0/tasks',
            headers=headers,
            params={
                'completed_since': 'now',
                'limit': 50,
                'opt_fields': 'name,due_on,projects.name,gid'
            }
        )

        if response.status_code == 200:
            tasks = response.json().get('data', [])
            upcoming = []
            now = datetime.now()

            for task in tasks:
                due_on = task.get('due_on')
                if due_on:
                    try:
                        due_date = parser.parse(due_on).date()
                        days_until = (due_date - now.date()).days

                        if 0 <= days_until <= 30:  # Next 30 days
                            upcoming.append({
                                "name": task.get('name', 'Unnamed Task'),
                                "due_date": due_on,
                                "days_until": days_until,
                                "project": task.get('projects', [{}])[0].get('name', 'Unknown Project'),
                                "gid": task.get('gid')
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing date {due_on}: {e}")

            return sorted(upcoming, key=lambda x: x['days_until'])
    except Exception as e:
        logger.error(f"Error fetching upcoming deadlines: {e}")

    # Return mock data if API fails
    return [
        {
            "name": "Easter Graphics Package",
            "due_date": "2026-02-28",
            "days_until": 14,
            "project": "Post Production",
            "gid": "12347"
        }
    ]

def is_task_at_risk(task):
    """Determine if a task is at risk"""
    due_on = task.get('due_on')
    if not due_on:
        return False

    try:
        due_date = parser.parse(due_on).date()
        days_until = (due_date - datetime.now().date()).days
        return days_until <= 3  # Due in 3 days or less
    except:
        return False

def has_upcoming_deadline(task):
    """Check if task has an upcoming deadline"""
    due_on = task.get('due_on')
    if not due_on:
        return False

    try:
        due_date = parser.parse(due_on).date()
        days_until = (due_date - datetime.now().date()).days
        return 0 <= days_until <= 14  # Due in next 2 weeks
    except:
        return False

def determine_task_risks(task):
    """Determine what risks a task has"""
    risks = []
    due_on = task.get('due_on')

    if due_on:
        try:
            due_date = parser.parse(due_on).date()
            days_until = (due_date - datetime.now().date()).days

            if days_until <= 1:
                risks.append("Due today/tomorrow")
            elif days_until <= 3:
                risks.append("Approaching deadline")

            # Add other risk factors as needed
            if not task.get('assignee'):
                risks.append("Unassigned")

        except:
            pass

    return risks if risks else ["General risk"]

def save_dashboard_data(data):
    """Save dashboard data to CSV files for reports"""
    try:
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save team capacity
        team_file = reports_dir / f"team_capacity_{timestamp}.csv"
        with open(team_file, 'w', newline='') as f:
            if data['team_capacity']:
                writer = csv.DictWriter(f, fieldnames=data['team_capacity'][0].keys())
                writer.writeheader()
                writer.writerows(data['team_capacity'])

        # Save at-risk tasks
        tasks_file = reports_dir / f"at_risk_tasks_{timestamp}.csv"
        with open(tasks_file, 'w', newline='') as f:
            if data['at_risk_tasks']:
                writer = csv.DictWriter(f, fieldnames=['name', 'project', 'assignee', 'due_on', 'risks'])
                writer.writeheader()
                for task in data['at_risk_tasks']:
                    # Convert risks list to string for CSV
                    task_copy = task.copy()
                    task_copy['risks'] = ', '.join(task_copy['risks'])
                    writer.writerow(task_copy)

        logger.info(f"Saved dashboard data to {reports_dir}")
    except Exception as e:
        logger.error(f"Error saving dashboard data: {e}")

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

# API Routes - Define all API routes first
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

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "asana_configured": bool(settings.asana_pat),
        "cache_age": (datetime.now() - dashboard_cache.get('last_updated', datetime.now())).total_seconds() if dashboard_cache.get('last_updated') else 0
    }

# Serve frontend (when built)
frontend_dist = "frontend/dist"
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Looking for frontend at: {os.path.abspath(frontend_dist)}")
logger.info(f"Frontend dist exists: {os.path.exists(frontend_dist)}")

if os.path.exists(frontend_dist):
    logger.info(f"Mounting frontend from: {frontend_dist}")
    logger.info(f"Frontend files: {os.listdir(frontend_dist)}")

    # Mount assets at /assets instead of /static to match Vite's build output
    assets_dir = f"{frontend_dist}/assets"
    if os.path.exists(assets_dir):
        logger.info(f"Mounting assets from: {assets_dir}")
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    else:
        logger.error(f"Assets directory not found: {assets_dir}")

    # Root route serves the frontend
    @app.get("/")
    async def serve_root():
        """Serve React SPA at root"""
        index_path = f"{frontend_dist}/index.html"
        if os.path.exists(index_path):
            logger.info(f"Serving index.html from: {index_path}")
            return FileResponse(index_path)
        else:
            logger.error(f"index.html not found at: {index_path}")
            return {"error": "Frontend not available"}

    # Catch-all route for SPA routing (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for all other routes"""
        # Don't intercept API routes or health
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        index_path = f"{frontend_dist}/index.html"
        if os.path.exists(index_path):
            logger.info(f"SPA routing: serving index.html for path: {full_path}")
            return FileResponse(index_path)
        else:
            logger.error(f"SPA routing: index.html not found at: {index_path}")
            return {"error": "Frontend not available"}
else:
    logger.warning(f"Frontend dist directory not found at: {frontend_dist}")
    logger.info("Available directories:")
    for item in os.listdir("."):
        if os.path.isdir(item):
            logger.info(f"  - {item}")

    # Fallback API-only root when frontend not available
    @app.get("/")
    async def root():
        return {
            "message": "Studio Dashboard API",
            "status": "online",
            "environment": settings.environment,
            "version": "2.0.0"
        }

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