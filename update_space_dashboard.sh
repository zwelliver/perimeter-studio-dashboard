#!/bin/bash
# Update Dashboard with Fresh Data

cd ~/Scripts/StudioProcesses
source venv/bin/activate

# Generate regular dashboard
python generate_dashboard.py

# Generate TV-optimized tabbed version
python generate_dashboard_tv_tabbed.py
