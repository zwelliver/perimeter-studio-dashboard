#!/usr/bin/env python3
"""
Simple FastAPI app for Studio Dashboard Railway deployment
"""
import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Studio Dashboard", version="2.0.0")

@app.get("/")
async def root():
    return {"message": "Studio Dashboard is running!", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy", "environment": "production"}

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "message": "API working"}

@app.get("/api/dashboard")
async def dashboard():
    return {
        "message": "Dashboard API placeholder",
        "status": "working",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "asana_configured": bool(os.getenv("ASANA_PAT"))
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Studio Dashboard on port {port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"ASANA_PAT configured: {bool(os.getenv('ASANA_PAT'))}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )