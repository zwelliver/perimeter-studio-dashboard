#!/bin/bash
# Auto-commit and push dashboard updates to GitHub

cd ~/Scripts/StudioProcesses

# Copy dashboard to root for cleaner URL (index.html)
cp Reports/capacity_dashboard.html index.html

# Check if dashboard was updated
if git diff --quiet Reports/capacity_dashboard.html index.html; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No dashboard changes to commit"
    exit 0
fi

# Commit and push the updated dashboard
git add Reports/capacity_dashboard.html index.html
git commit -m "Update capacity dashboard - $(date '+%Y-%m-%d %H:%M')"

# Try to push to GitHub
if git push origin main 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Dashboard updated on GitHub successfully"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Failed to push to GitHub. Check authentication."
    exit 1
fi
