#!/usr/bin/env python3
"""
Helper script to apply space theme to generate_dashboard.py
This script reads the experiment HTML and generate_dashboard.py,
then creates a new version with the space theme integrated.
"""

import re
from pathlib import Path

def main():
    # Read the experiment file (has space theme styling)
    experiment_path = Path('/Users/comstudio/Scripts/StudioProcesses/Reports/capacity_dashboard_experiment.html')
    experiment_content = experiment_path.read_text()

    # Read the current generator
    generator_path = Path('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py')
    generator_content = generator_path.read_text()

    # Extract just the CSS from the experiment file (between <style> and </style>)
    style_match = re.search(r'<style>(.*?)</style>', experiment_content, re.DOTALL)
    if not style_match:
        print("ERROR: Could not find style section in experiment file")
        return

    space_theme_css = style_match.group(1)

    # Now we need to replace the CSS in generate_dashboard.py
    # The template starts at line 919 with: html = f"""<!DOCTYPE html>
    # The style section is between <style> and </style>

    # Find the current style section in generator
    generator_style_pattern = r'(<style>)(.*?)(</style>)'

    def replace_style(match):
        # Keep the opening and closing tags, replace the content
        # But we need to escape curly braces for f-string: {{ and }}
        escaped_css = space_theme_css.replace('{', '{{').replace('}', '}}')
        return match.group(1) + escaped_css + match.group(3)

    # Replace the style section
    new_generator = re.sub(generator_style_pattern, replace_style, generator_content, flags=re.DOTALL)

    # Also need to add the space visual effects elements right after <body>
    # Extract the visual effects from experiment (lines 1527-1572)
    visual_effects_match = re.search(r'<body>\s*<!-- Space visual effects -->.*?<!-- Constellation pattern -->.*?</div>\s*<div class="dashboard-container">', experiment_content, re.DOTALL)

    if visual_effects_match:
        visual_effects = visual_effects_match.group(0)
        # Remove the closing <div class="dashboard-container"> part
        visual_effects = visual_effects.replace('<div class="dashboard-container">', '').strip()

        # Escape for f-string
        visual_effects_escaped = visual_effects.replace('{', '{{').replace('}', '}}')

        # Insert after <body>, removing any duplicate <body> tags in the visual effects
        visual_effects_cleaned = re.sub(r'<body>\s*', '', visual_effects_escaped)

        # Insert after <body>
        new_generator = re.sub(
            r'(<body>)\s*(<div class="dashboard-container">)',
            r'\1\n    ' + visual_effects_cleaned + '\n\n    \\2',
            new_generator
        )

    # Update the header to include the space theme decorations
    new_generator = new_generator.replace(
        '<h1>Perimeter Studio Dashboard</h1>',
        '<h1>✦ Perimeter Studio Dashboard ✦</h1>'
    )

    new_generator = new_generator.replace(
        '<div class="timestamp">Last Updated: {data[\'timestamp\']}</div>',
        '<div class="timestamp">⟡ Last Updated: {data[\'timestamp\']}</div>'
    )

    # Save the updated generator
    output_path = Path('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py')
    output_path.write_text(new_generator)

    print("✅ Successfully applied space theme to generate_dashboard.py")
    print("   - Updated CSS styling with space theme")
    print("   - Added space visual effects (nebulas, shooting stars, particles)")
    print("   - Updated header decorations")

if __name__ == "__main__":
    main()
