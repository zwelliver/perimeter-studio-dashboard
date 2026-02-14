#!/usr/bin/env python3
"""
Minimal FastAPI test for Railway deployment
"""
import os
import logging
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Studio Dashboard Test", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Studio Dashboard API is running!", "environment": "Railway"}

@app.get("/health")
async def health():
    return {"status": "healthy", "port": os.getenv("PORT", "unknown")}

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "message": "API working"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting test server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")