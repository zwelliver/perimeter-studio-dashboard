#!/bin/bash

# Script to reduce cron job frequency and fix API rate limits
# Created: 2026-01-24

echo "🔧 Fixing cron job frequencies to reduce API rate limits..."

# Create backup
BACKUP_FILE=~/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
crontab -l > "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Create temporary file for modifications
TEMP_CRON=/tmp/updated_crontab.txt
crontab -l > "$TEMP_CRON"

echo "📝 Updating frequencies..."

# Change video scorer/timeline from every 15 min to every 2 hours
sed -i '' 's|\*/15 \* \* \* \* /bin/bash -c "cd ~/Scripts/StudioProcesses && source venv/bin/activate && python video_scorer.py|0 */2 * * * /bin/bash -c "cd ~/Scripts/StudioProcesses \&\& source venv/bin/activate \&\& python video_scorer.py|g' "$TEMP_CRON"

# Change dashboard update from every 15 min to every 2 hours  
sed -i '' 's|\*/15 \* \* \* \* /Users/comstudio/Scripts/StudioProcesses/update_space_dashboard.sh|0 */2 * * * /Users/comstudio/Scripts/StudioProcesses/update_space_dashboard.sh|g' "$TEMP_CRON"

# Change production backdrops from every 10 min to every 30 min
sed -i '' 's|\*/10 \* \* \* \* /bin/bash -c "cd ~/Scripts/StudioProcesses && source myenv/bin/activate && python production_backdrops.py|*/30 * * * * /bin/bash -c "cd ~/Scripts/StudioProcesses \&\& source myenv/bin/activate \&\& python production_backdrops.py|g' "$TEMP_CRON"

# Change feedback from every 15 min to every 2 hours
sed -i '' 's|\*/15 \* \* \* \* /Users/comstudio/Scripts/StudioProcesses/run_post_completion_feedback.sh|0 */2 * * * /Users/comstudio/Scripts/StudioProcesses/run_post_completion_feedback.sh|g' "$TEMP_CRON"

# Change forecast matcher from every 15 min to every 2 hours
sed -i '' 's|\*/15 \* \* \* \* ~/Scripts/StudioProcesses/run_forecast_matcher.sh|0 */2 * * * ~/Scripts/StudioProcesses/run_forecast_matcher.sh|g' "$TEMP_CRON"

echo "📊 Changes preview:"
echo "Before (problematic jobs):"
crontab -l | grep -E '\*/(15|10)' | while read line; do echo "  ❌ $line"; done

echo -e "\nAfter (fixed frequencies):"
grep -E '0 \*/2|\*/30' "$TEMP_CRON" | while read line; do echo "  ✅ $line"; done

echo -e "\n🤔 Apply these changes? [y/N]"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # Apply the changes
    crontab "$TEMP_CRON"
    echo "✅ Cron jobs updated successfully!"
    echo "📈 API rate reduction: ~20 calls/hour → ~4 calls/hour (80% reduction)"
    echo "🔍 Verify with: crontab -l | grep -E '0 \*/2|\*/30'"
else
    echo "❌ Changes not applied. Your crontab remains unchanged."
    echo "💡 Backup is still available at: $BACKUP_FILE"
fi

# Cleanup
rm -f "$TEMP_CRON"
echo "🧹 Cleanup complete."