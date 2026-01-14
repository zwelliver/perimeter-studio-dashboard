"""Fix CSS braces in the merged dashboard file"""

# Read the file
with open('generate_dashboard.py', 'r') as f:
    content = f.read()

# Find the new chart CSS section (between PROGRESS RING STYLES and the next </style>)
import re

# Fix lines 1510-1800 approximately (the new chart CSS section)
lines = content.split('\n')
fixed_lines = []
in_new_css = False

for i, line in enumerate(lines):
    # Detect start of new CSS section
    if '/* ===== PROGRESS RING STYLES =====' in line:
        in_new_css = True

    # Detect end of new CSS section (when we hit typing-indicator or </style> after the new CSS)
    if in_new_css and ('typing-indicator' in line or (i > 1800 and '</style>' in line)):
        in_new_css = False

    # Fix braces in the new CSS section
    if in_new_css and i > 1509:
        # Replace single { with {{ and single } with }} but only for CSS rules
        # Don't touch lines that are already using {{ or }}
        if '{' in line and '{{' not in line and not line.strip().startswith('/*') and not line.strip().startswith('*'):
            line = line.replace('{', '{{')
        if '}' in line and '}}' not in line and not line.strip().startswith('/*') and not line.strip().startswith('*'):
            line = line.replace('}', '}}')

    fixed_lines.append(line)

# Write back
with open('generate_dashboard.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed CSS braces!")
