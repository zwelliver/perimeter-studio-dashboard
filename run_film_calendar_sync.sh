#!/bin/bash
# Wrapper script to run both Film Date and Due Date calendar syncs from cron

# Change to script directory
cd /Users/comstudio/Scripts/StudioProcesses

# Activate virtual environment and run film date sync
source venv/bin/activate && python3 film_date_calendar_sync.py >> film_calendar_sync.log 2>&1

# Add timestamp to film date log
echo "----------------------------------------" >> film_calendar_sync.log
echo "Film Date sync completed at $(date)" >> film_calendar_sync.log
echo "" >> film_calendar_sync.log

# Run due date sync
source venv/bin/activate && python3 due_date_calendar_sync.py >> due_calendar_sync.log 2>&1

# Add timestamp to due date log
echo "----------------------------------------" >> due_calendar_sync.log
echo "Due Date sync completed at $(date)" >> due_calendar_sync.log
echo "" >> due_calendar_sync.log
