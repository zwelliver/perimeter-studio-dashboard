#!/bin/bash
# Start Studio Command Center Backend API

cd "$(dirname "$0")"

echo "🎬 Studio Command Center - Backend API"
echo "======================================"
echo ""

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start the API
echo ""
echo "Starting API server..."
python app.py
