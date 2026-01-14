#!/bin/bash
# Update Dashboard with Fresh Data and Push to GitHub

cd ~/Scripts/StudioProcesses
source venv/bin/activate

# Generate regular dashboard
python generate_dashboard.py

# Generate TV-optimized tabbed version
python generate_dashboard_tv_tabbed.py

# Commit and push changes to GitHub
git add Reports/capacity_dashboard.html Reports/Combined_heatmap_weighted.png .gitignore README.md

# Only commit if there are changes
if git diff --staged --quiet; then
    echo "No dashboard changes to commit"
else
    git commit -m "$(cat <<'EOF'
Update dashboard with latest data

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" && git push
    echo "Dashboard changes pushed to GitHub"
fi
