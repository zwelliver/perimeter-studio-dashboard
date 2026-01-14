"""Remove space theme CSS and keep clean Perimeter styling"""

# Read the space theme file
with open('generate_dashboard_space.py', 'r') as f:
    lines = f.readlines()

# Find line numbers for problematic CSS sections
remove_start = None
remove_end = None

for i, line in enumerate(lines):
    # Find body::before (start of space decorations)
    if remove_start is None and 'body::before' in line:
        remove_start = i
    # Find .dashboard-container (end of space decorations)
    if remove_start is not None and '.dashboard-container {{' in line:
        remove_end = i
        break

if remove_start and remove_end:
    print(f"Removing space decorations from line {remove_start} to {remove_end-1}")
    # Remove the lines
    new_lines = lines[:remove_start] + ['\n'] + lines[remove_end:]
else:
    new_lines = lines
    print("Could not find space decoration section")

# Also need to simplify card styles - replace dark glowing cards with clean white cards
final_lines = []
skip_until_close = False

for i, line in enumerate(new_lines):
    # Simplify card background from dark/glowing to white
    if '.card {{' in line:
        # Read ahead to find the closing brace and replace whole card section
        card_lines = [line]
        depth = 1
        j = i + 1
        while j < len(new_lines) and depth > 0:
            card_lines.append(new_lines[j])
            if '{{' in new_lines[j]:
                depth += 1
            if '}}' in new_lines[j]:
                depth -= 1
            j += 1

        # Replace with simple Perimeter card style
        final_lines.append('        .card {{\n')
        final_lines.append('            background: white;\n')
        final_lines.append('            padding: 25px;\n')
        final_lines.append('            border-radius: 12px;\n')
        final_lines.append('            box-shadow: 0 2px 8px rgba(0,0,0,0.1);\n')
        final_lines.append('        }}\n')
        final_lines.append('\n')

        # Skip the original card lines
        for _ in range(len(card_lines) - 1):
            next(enumerate(new_lines[i+1:]), None)
        continue

    final_lines.append(line)

# Write the cleaned version
with open('generate_dashboard.py', 'w') as f:
    f.writelines(final_lines)

print("✅ CSS cleaned! Removed space decorations and simplified cards.")
