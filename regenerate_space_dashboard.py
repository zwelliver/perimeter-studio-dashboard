#!/usr/bin/env python3
"""
Regenerate Space-Themed Dashboard
Updates the space-themed dashboard with fresh data while preserving the design
"""

import subprocess
import re
from datetime import datetime
from pathlib import Path

def main():
    print("🌌 Regenerating Space-Themed Dashboard...")

    # Step 1: Generate fresh data using the original script
    print("📊 Generating fresh data...")
    subprocess.run(['python', 'generate_dashboard.py'], check=True, cwd='/Users/comstudio/Scripts/StudioProcesses')

    # Step 2: The freshly generated dashboard already has the latest data
    # We just need to update the timestamp and keep the file as-is
    dashboard_path = Path('/Users/comstudio/Scripts/StudioProcesses/Reports/capacity_dashboard.html')
    dashboard_content = dashboard_path.read_text()

    # Extract timestamp
    timestamp_match = re.search(r'Last Updated: ([^<]+)</div>', dashboard_content)
    fresh_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%B %d, %Y at %I:%M %p')

    # The dashboard is already up-to-date from generate_dashboard.py
    result = dashboard_content
    output_path = dashboard_path

    print(f"✅ Dashboard updated: {output_path}")
    print(f"🕐 Timestamp: {fresh_timestamp}")

    # Step 6: Optional - Auto-commit to GitHub
    print("\n📤 Pushing to GitHub...")
    subprocess.run([
        'git', 'add', 'Reports/capacity_dashboard.html'
    ], cwd='/Users/comstudio/Scripts/StudioProcesses', check=True)

    subprocess.run([
        'git', 'commit', '-m', f'Update space dashboard - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    ], cwd='/Users/comstudio/Scripts/StudioProcesses')

    subprocess.run([
        'git', 'push', 'origin', 'main'
    ], cwd='/Users/comstudio/Scripts/StudioProcesses', check=True)

    print("✅ Dashboard pushed to GitHub!")
    print("\n🌟 Done! Your space-themed dashboard has been updated with fresh data!")

if __name__ == "__main__":
    main()
