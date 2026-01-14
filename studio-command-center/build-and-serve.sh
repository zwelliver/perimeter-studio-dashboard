#!/bin/bash
# Build and Serve Studio Command Center

echo "=========================================="
echo "🎬 Studio Command Center"
echo "=========================================="
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build

# Go back to root
cd ..

# Start backend (which will serve the built frontend)
echo ""
echo "🚀 Starting server..."
echo "📡 Command Center will be available at: http://localhost:5000"
echo ""
cd backend
./start.sh
