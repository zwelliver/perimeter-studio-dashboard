#!/bin/bash
# ============================================
# Setup Script for New Studio Automations
# ============================================
#
# This script will:
# 1. Create the "Forecast Status" custom field in Asana
# 2. Show you the cron entries to add
#
# Run this script on your server where the automations will run.
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "Perimeter Studio - New Automations Setup"
echo "============================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Error: venv directory not found"
    echo "   Please create a virtual environment first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Step 1: Create the Forecast Status custom field
echo ""
echo "Step 1: Creating 'Forecast Status' custom field in Asana..."
echo "--------------------------------------------"
python3 setup_forecast_status_field.py

# Step 2: Show cron setup instructions
echo ""
echo "============================================"
echo "Step 2: Set up cron jobs"
echo "============================================"
echo ""
echo "Run 'crontab -e' and add these lines:"
echo ""
echo "# Forecast Status Automation - every 30 minutes"
echo "*/30 * * * * cd $SCRIPT_DIR && ./run_forecast_status_automation.sh >> logs/forecast_status.log 2>&1"
echo ""
echo "# Post-Completion Feedback - every 15 minutes"
echo "*/15 * * * * cd $SCRIPT_DIR && ./run_post_completion_feedback.sh >> logs/feedback.log 2>&1"
echo ""
echo "============================================"
echo "Setup complete!"
echo ""
echo "You can test the automations manually:"
echo "  ./run_forecast_status_automation.sh"
echo "  ./run_post_completion_feedback.sh"
echo "============================================"
