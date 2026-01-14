"""
Script to merge dashboards: take space theme structure with Perimeter CSS
"""

# Read both files
with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py', 'r') as f:
    original_content = f.read()

with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard_space.py', 'r') as f:
    space_content = f.read()

# Extract the original Perimeter CSS (between <style> and </style>)
# Find positions
orig_style_start = original_content.find('    <style>')
orig_style_end = original_content.find('    </style>', orig_style_start)
original_css_section = original_content[orig_style_start:orig_style_end + len('    </style>')]

# Extract the space theme CSS section
space_style_start = space_content.find('    <style>')
space_style_end = space_content.find('    </style>', space_style_start)

# We need to add new chart styles to Perimeter CSS
# Extract new chart CSS from space theme (Progress Rings, Timeline, Radar, Velocity, Heatmap)
new_chart_css = """
        /* ===== PROGRESS RING STYLES ===== */
        .progress-rings-container {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 30px;
            margin: 20px 0;
            padding: 20px;
            overflow: visible;
        }}

        .progress-ring {{
            position: relative;
            width: 160px;
            height: 160px;
        }}

        .progress-ring-svg {{
            transform: rotate(-90deg);
        }}

        .progress-ring-circle {{
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
        }}

        .progress-ring-bg {{
            stroke: #e9ecef;
        }}

        .progress-ring-progress {{
            transition: stroke-dashoffset 2s ease;
        }}

        .progress-ring-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .progress-ring-value {{
            font-size: 28px;
            font-weight: 700;
            color: #09243F;
            display: block;
        }}

        .progress-ring-label {{
            font-size: 11px;
            color: #6c757d;
            display: block;
            margin-top: 4px;
        }}

        /* ===== TIMELINE GANTT STYLES ===== */
        .timeline-container {{
            margin: 20px 0;
            overflow-x: auto;
            position: relative;
        }}

        .timeline-header {{
            display: flex;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #60BBE9;
        }}

        .timeline-project-col {{
            min-width: 200px;
            font-weight: 600;
            color: #09243F;
        }}

        .timeline-dates {{
            display: flex;
            flex: 1;
            min-width: 600px;
        }}

        .timeline-date {{
            flex: 1;
            text-align: center;
            font-size: 11px;
            color: #6c757d;
        }}

        .timeline-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            min-height: 40px;
        }}

        .timeline-project-name {{
            min-width: 200px;
            font-size: 13px;
            color: #09243F;
            padding-right: 15px;
        }}

        .timeline-bars {{
            display: flex;
            flex: 1;
            min-width: 600px;
            position: relative;
            height: 40px;
        }}

        .timeline-bar {{
            position: absolute;
            height: 24px;
            border-radius: 12px;
            background: linear-gradient(90deg, #60BBE9, #4a9fd8);
            border: 2px solid #60BBE9;
            box-shadow: 0 2px 8px rgba(96, 187, 233, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            overflow: hidden;
        }}

        .timeline-bar:hover {{
            transform: scaleY(1.2);
            box-shadow: 0 4px 12px rgba(96, 187, 233, 0.5);
        }}

        .timeline-bar.critical {{
            background: linear-gradient(90deg, #dc3545, #c82333);
            border-color: #dc3545;
            box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
        }}

        .timeline-bar.critical:hover {{
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.5);
        }}

        .timeline-bar.warning {{
            background: linear-gradient(90deg, #ffc107, #e0a800);
            border-color: #ffc107;
            box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
        }}

        .timeline-bar.warning:hover {{
            box-shadow: 0 4px 12px rgba(255, 193, 7, 0.5);
        }}

        /* ===== RADAR/SPIDER CHART STYLES ===== */
        .radar-container {{
            position: relative;
            width: 500px;
            height: 500px;
            margin: 20px auto;
        }}

        .radar-svg {{
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
        }}

        .radar-grid {{
            fill: none;
            stroke: #dee2e6;
            stroke-width: 1;
        }}

        .radar-axis {{
            stroke: #dee2e6;
            stroke-width: 1;
        }}

        .radar-area {{
            fill: rgba(96, 187, 233, 0.3);
            stroke: #60BBE9;
            stroke-width: 2;
        }}

        .radar-target {{
            fill: rgba(220, 53, 69, 0.1);
            stroke: #dc3545;
            stroke-width: 2;
            stroke-dasharray: 5, 5;
        }}

        .radar-label {{
            fill: #09243F;
            font-size: 12px;
            font-weight: 600;
            text-anchor: middle;
        }}

        /* ===== VELOCITY TREND CHART ===== */
        .velocity-container {{
            position: relative;
            height: 300px;
            margin: 20px 0;
        }}

        /* ===== HEAT MAP CALENDAR STYLES ===== */
        .heatmap-calendar {{
            display: grid;
            grid-template-columns: auto repeat(10, 1fr);
            gap: 4px;
            margin: 20px 0;
        }}

        .heatmap-day-label {{
            font-size: 11px;
            color: #6c757d;
            padding: 8px 12px;
            text-align: right;
        }}

        .heatmap-date {{
            font-size: 10px;
            color: #6c757d;
            text-align: center;
            margin-bottom: 4px;
        }}

        .heatmap-cell {{
            aspect-ratio: 1;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }}

        .heatmap-cell:hover {{
            transform: scale(1.15);
            z-index: 10;
        }}

        .heatmap-cell.intensity-0 {{
            background: #f8f9fa;
            color: #6c757d;
        }}

        .heatmap-cell.intensity-1 {{
            background: rgba(96, 187, 233, 0.2);
            box-shadow: 0 0 5px rgba(96, 187, 233, 0.2);
            color: #60BBE9;
        }}

        .heatmap-cell.intensity-2 {{
            background: rgba(96, 187, 233, 0.4);
            box-shadow: 0 0 8px rgba(96, 187, 233, 0.3);
            color: white;
        }}

        .heatmap-cell.intensity-3 {{
            background: rgba(255, 193, 7, 0.6);
            box-shadow: 0 0 8px rgba(255, 193, 7, 0.3);
            color: white;
        }}

        .heatmap-cell.intensity-4 {{
            background: rgba(220, 53, 69, 0.7);
            box-shadow: 0 0 10px rgba(220, 53, 69, 0.4);
            color: white;
        }}
"""

# Insert new chart CSS before </style> in original CSS
original_css_with_charts = original_css_section.replace('    </style>', new_chart_css + '\n    </style>')

# Replace space theme CSS with modified original CSS
merged_content = space_content[:space_style_start] + original_css_with_charts + space_content[space_style_end + len('    </style>'):]

# Write merged file
with open('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py', 'w') as f:
    f.write(merged_content)

print("✅ Successfully merged dashboards!")
print("   - Used Perimeter CSS styling from original")
print("   - Added new chart styles (Progress Rings, Timeline, Radar, Velocity, Heatmap)")
print("   - Kept all data processing and charts from space theme")
