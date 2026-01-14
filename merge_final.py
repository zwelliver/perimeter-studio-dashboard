"""
Final merge script with proper brace escaping
"""

# Read both files
with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py.backup' if False else '/Users/comstudio/Scripts/StudioProcesses/generate_dashboard_space.py', 'r') as f:
    space_content = f.read()

with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py.backup' if False else '/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py.original' if False else '/Users/comstudio/Scripts/StudioProcesses/generate_dashboard_backup.py', 'r') as f:
    backup_content = f.read()

# Actually, simpler approach - just manually create the final CSS section
# Let me read the original perimeter file from the copy we know works
print("Reading original Perimeter file...")
with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard_backup.py', 'r') as f:
    lines = f.readlines()

# Find CSS section in original
css_start = None
css_end = None
for i, line in enumerate(lines):
    if '<style>' in line and css_start is None:
        css_start = i
    if '</style>' in line and css_start is not None and css_end is None:
        css_end = i
        break

print(f"Original space theme CSS: lines {css_start} to {css_end}")

# Read the original Perimeter dashboard to get its CSS
# But wait - we don't have the original anymore. Let me check what files we have
import os
files = os.listdir('.')
dashboard_files = [f for f in files if 'generate_dashboard' in f and f.endswith('.py')]
print(f"Dashboard files: {dashboard_files}")
