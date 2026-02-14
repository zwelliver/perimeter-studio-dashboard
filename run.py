#!/usr/bin/env python3
"""
Studio Command Center - FastAPI Server Runner
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 Studio Command Center API Starting (FastAPI)...")
    print("=" * 60)
    print(f"📡 API will be available at: http://localhost:5001")
    print(f"📊 Dashboard endpoint: http://localhost:5001/api/dashboard")
    print(f"💚 Health check: http://localhost:5001/api/status")
    print(f"📖 API docs: http://localhost:5001/docs")
    print("=" * 60)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5001,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )