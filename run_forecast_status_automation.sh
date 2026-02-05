#!/bin/bash
# Run the Forecast Status Automation
# Automatically moves tasks from Forecast to Preproduction when status is "Ready for Preproduction"

cd "$(dirname "$0")"
source venv/bin/activate
python3 forecast_status_automation.py
