#!/usr/bin/env python3
"""
TV-Optimized Tabbed Dashboard Generator
Creates a multi-page tabbed interface for large TV displays
"""

import sys
import os
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main dashboard generator
from generate_dashboard import read_reports, generate_html_dashboard

def transform_kpi_to_metrics(card):
    """Transform KPI card from progress rings to simple metric list"""
    # Extract the metric labels from the card
    labels = card.find_all('span', class_='progress-ring-label')

    # Create a new card with simple metrics matching Performance Overview style
    kpi_html = '''
    <div class="card">
        <h2>📊 Key Performance Metrics</h2>
        <div class="metric">
            <span class="metric-label">On-Time Delivery</span>
            <span class="metric-value" id="ringOnTimeValue">0%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Team Utilization</span>
            <span class="metric-value" id="ringUtilizationValue">0%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Active Projects</span>
            <span class="metric-value" id="ringProjectsValue">0</span>
        </div>
    </div>
    '''
    return kpi_html

def create_tabbed_tv_dashboard(html):
    """Transform regular dashboard into tabbed TV interface"""

    soup = BeautifulSoup(html, 'html.parser')

    # Find all cards
    cards = soup.find_all('div', class_='card')

    # Categorize cards by their heading text
    overview_cards = []
    project_cards = []
    capacity_cards = []
    allocation_cards = []

    for card in cards:
        # Get the card's h2 heading to categorize it
        heading = card.find('h2')
        if not heading:
            continue

        heading_text = heading.get_text().strip()

        # Overview: Performance overview, KPI, contracted/outsourced, at-risk
        if heading_text == 'Performance Overview':
            overview_cards.append(str(card))
        elif 'Key Performance' in heading_text:
            overview_cards.append(transform_kpi_to_metrics(card))
        elif heading_text == 'Contracted/Outsourced Projects':
            overview_cards.append(str(card))
        elif 'At-Risk' in heading_text:
            overview_cards.append(str(card))

        # Projects: Upcoming shoots, upcoming deadlines, project timeline, workload balance
        elif 'Upcoming Shoot' in heading_text:
            project_cards.append(str(card))
        elif 'Upcoming Project Deadline' in heading_text:
            project_cards.append(str(card))
        elif heading_text == 'Project Timeline':
            project_cards.append(str(card))
        elif heading_text == 'Workload Balance':
            # Add to both Projects and Allocation tabs
            card_html = str(card).replace('class="card full-width"', 'class="card"')
            project_cards.append(card_html)
            allocation_cards.append(card_html)

        # Capacity: Team capacity, velocity, 10-day heatmap, capacity utilization, 6-month timeline, historical capacity
        elif heading_text == 'Team Capacity':
            capacity_cards.append(str(card))
        elif 'Team Velocity' in heading_text or 'Velocity Trend' in heading_text:
            capacity_cards.append(str(card))
        elif 'Workload Heat Map' in heading_text:
            capacity_cards.append(str(card))
        elif 'Capacity Utilization' in heading_text:
            capacity_cards.append(str(card))
        elif '6-Month Capacity' in heading_text or '6 Month' in heading_text:
            capacity_cards.append(str(card))
        elif heading_text == '📈 Historical Capacity Utilization':
            capacity_cards.append(str(card))

        # Allocation: workload balance (already added above), category cards, historical allocation
        elif heading_text in ['Communications', 'Creative Resources', 'Partners', 'Pastoral/Strategic', 'Spiritual Formation', 'Technical Execution']:
            allocation_cards.append(str(card))
        elif 'Historical Allocation Trends' in heading_text:
            allocation_cards.append(str(card))

        else:
            # Any remaining cards default to overview
            print(f"Warning: Uncategorized card: {heading_text}")
            overview_cards.append(str(card))

    # Build content for each tab with 2x2 grid layouts
    # Overview: Performance overview, KPI, contracted/outsourced, at-risk (2x2 grid)
    overview_content = '<div class="grid">'
    for card_html in overview_cards:
        cleaned_card = card_html.replace('class="card full-width"', 'class="card"')
        overview_content += cleaned_card
    overview_content += '</div>'

    # Projects content (2x2 grid for main cards)
    projects_content = '<div class="grid">' + ''.join(project_cards) + '</div>'

    # Capacity content - special ordering and team capacity full width
    # Order: Team Capacity (full width), Velocity, Heatmap, 30-day utilization, 6-month timeline, Historical
    capacity_content = '<div class="grid">'

    # Find and categorize capacity cards
    team_capacity_card = None
    velocity_card = None
    heatmap_card = None
    utilization_30_card = None
    timeline_6m_card = None
    historical_cap_card = None

    for card_html in capacity_cards:
        if 'Team Capacity</h2>' in card_html:
            # Make team capacity full width
            team_capacity_card = card_html.replace('class="card"', 'class="card full-width"')
        elif 'Velocity' in card_html:
            velocity_card = card_html
        elif 'Heat Map' in card_html:
            heatmap_card = card_html
        elif 'Next 30 Days' in card_html:
            utilization_30_card = card_html
        elif '6-Month' in card_html or '6 Month' in card_html:
            timeline_6m_card = card_html
        elif 'Historical Capacity' in card_html:
            historical_cap_card = card_html

    # Add in desired order
    if team_capacity_card:
        capacity_content += team_capacity_card
    if velocity_card:
        capacity_content += velocity_card
    if heatmap_card:
        capacity_content += heatmap_card
    if utilization_30_card:
        capacity_content += utilization_30_card
    if timeline_6m_card:
        capacity_content += timeline_6m_card
    if historical_cap_card:
        capacity_content += historical_cap_card

    capacity_content += '</div>'

    # Allocation content (radar + categories in row, then historical chart below)
    allocation_content = '<div class="grid">' + ''.join(allocation_cards) + '</div>'

    # Create tabbed HTML structure
    tabbed_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perimeter Studio Dashboard - TV View</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {get_tv_styles()}
    </style>
</head>
<body>
    <div class="tv-tabs">
        <button class="tv-tab active" id="overview-tab" onclick="showTab('overview')">
            📊 Overview
        </button>
        <button class="tv-tab" id="projects-tab" onclick="showTab('projects')">
            📅 Projects
        </button>
        <button class="tv-tab" id="capacity-tab" onclick="showTab('capacity')">
            👥 Capacity
        </button>
        <button class="tv-tab" id="allocation-tab" onclick="showTab('allocation')">
            📈 Allocation
        </button>
    </div>

    <div class="tv-content active" id="overview-content">
        <h1 class="tab-title">Studio Overview</h1>
        {overview_content}
    </div>

    <div class="tv-content" id="projects-content">
        <h1 class="tab-title">Projects & Timeline</h1>
        {projects_content}
    </div>

    <div class="tv-content" id="capacity-content">
        <h1 class="tab-title">Team Capacity & Forecast</h1>
        {capacity_content}
    </div>

    <div class="tv-content" id="allocation-content">
        <h1 class="tab-title">Resource Allocation</h1>
        {allocation_content}
    </div>

    <div class="keyboard-hint">
        ← → Arrow keys to navigate
    </div>

    <script>
        {get_tv_scripts()}
    </script>
</body>
</html>
"""

    return tabbed_html

def get_tv_styles():
    """Get CSS styles for TV interface"""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            overflow: hidden;
        }

        /* Tab Navigation */
        .tv-tabs {
            display: flex;
            background: #09243F;
            padding: 0;
            margin: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }

        .tv-tab {
            flex: 1;
            padding: 20px 20px;
            color: rgba(255,255,255,0.7);
            font-size: 19px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            border: none;
            background: transparent;
            border-bottom: 4px solid transparent;
            transition: all 0.3s ease;
        }

        .tv-tab:hover {
            background: rgba(255,255,255,0.05);
            color: rgba(255,255,255,0.9);
        }

        .tv-tab.active {
            color: #60BBE9;
            border-bottom-color: #60BBE9;
            background: rgba(96,187,233,0.1);
        }

        /* Tab Content */
        .tv-content {
            display: none;
            padding: 90px 30px 20px 30px;
            height: 100vh;
            overflow: hidden;
            box-sizing: border-box;
        }

        .tv-content.active {
            display: flex;
            flex-direction: column;
        }

        .tab-title {
            color: #09243F;
            font-size: 24px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 3px solid #60BBE9;
            flex-shrink: 0;
        }

        /* Grid layout - 2 columns for optimal readability */
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 18px;
            flex: 1;
            overflow-y: auto;
            align-content: start;
            padding-right: 10px;
        }

        /* Card styling */
        .card {
            background: white;
            padding: 20px 24px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
            max-height: 480px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        /* Larger height for radar chart card */
        .card:has(.radar-container) {
            max-height: 500px;
            height: 100%;
            overflow: visible;
        }

        /* Larger height for timeline and shoots cards */
        .card:has(.timeline-container),
        .card:has([style*="grid-template-columns"]) {
            max-height: 520px;
        }

        .card h2 {
            color: #09243F;
            font-size: 20px;
            margin-bottom: 14px;
            font-weight: 600;
            border-bottom: 2px solid #60BBE9;
            padding-bottom: 10px;
            flex-shrink: 0;
        }

        .card h3 {
            font-size: 16px;
            color: #09243F;
            margin: 12px 0 10px 0;
        }

        .card p {
            font-size: 15px;
        }

        .full-width {
            grid-column: 1 / -1;
            max-height: 450px;
        }

        /* Metrics */
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid #dee2e6;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-size: 16px;
            color: #6c757d;
            font-weight: 500;
        }

        .metric-value {
            font-size: 24px;
            font-weight: 700;
            color: #60BBE9;
        }

        .metric-value.positive { color: #28a745; }
        .metric-value.negative { color: #dc3545; }
        .metric-value.warning { color: #ffc107; }

        /* Progress Rings */
        .progress-rings-container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
            margin: 12px 0;
            padding: 12px;
        }

        .progress-ring {
            position: relative;
            width: 120px;
            height: 120px;
            text-align: center;
        }

        .progress-ring-svg {
            transform: rotate(-90deg);
        }

        .progress-ring-circle {
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
        }

        .progress-ring-bg {
            stroke: #e9ecef;
        }

        .progress-ring-progress {
            transition: stroke-dashoffset 2s ease;
        }

        .progress-ring-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            width: 120px;
        }

        .progress-ring svg {
            width: 120px !important;
            height: 120px !important;
        }

        .progress-ring-value {
            font-size: 20px;
            font-weight: 700;
            color: #09243F;
            display: block;
            line-height: 1;
        }

        .progress-ring-label {
            font-size: 9px;
            color: #6c757d;
            display: block;
            margin-top: 4px;
            line-height: 1.2;
        }

        /* Charts */
        .chart-container {
            position: relative;
            height: 220px;
            margin-top: 10px;
        }

        canvas {
            max-height: 220px !important;
        }

        /* Timeline */
        .timeline-container {
            margin: 10px 0;
            overflow-x: auto;
            min-height: 200px;
        }

        .timeline-header {
            display: flex;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #dee2e6;
        }

        .timeline-project-col {
            min-width: 220px;
            font-weight: 600;
            color: #09243F;
            font-size: 14px;
            padding-right: 15px;
            border-right: 2px solid #dee2e6;
            margin-right: 15px;
        }

        .timeline-dates {
            display: flex;
            flex: 1;
            min-width: 600px;
        }

        .timeline-date {
            flex: 1;
            text-align: center;
            font-size: 13px;
            color: #6c757d;
            font-weight: 500;
        }

        .timeline-row {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            min-height: 36px;
        }

        .timeline-project-name {
            min-width: 220px;
            font-size: 14px;
            color: #09243F;
            padding-right: 15px;
            font-weight: 500;
            border-right: 2px solid #dee2e6;
            margin-right: 15px;
        }

        .timeline-bars {
            display: flex;
            flex: 1;
            min-width: 600px;
            position: relative;
            height: 30px;
        }

        .timeline-bar {
            position: absolute;
            height: 24px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            font-weight: 600;
            padding: 0 6px;
        }

        .timeline-bar.critical {
            background: #dc3545;
        }

        .timeline-bar.warning {
            background: #ffc107;
        }

        .timeline-bar.normal {
            background: #60BBE9;
        }

        .timeline-bar.info {
            background: #17a2b8;
        }

        /* Heatmaps */
        .heatmap-grid {
            margin-top: 15px;
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 5px;
        }

        /* Heatmap Calendar - Workload */
        .heatmap-calendar {
            display: grid;
            grid-template-columns: auto repeat(10, 1fr);
            gap: 4px;
            margin: 20px 0;
        }

        .heatmap-day-label {
            font-size: 11px;
            color: #6c757d;
            padding: 8px 12px;
            text-align: right;
            font-weight: 600;
        }

        .heatmap-date {
            font-size: 10px;
            color: #6c757d;
            text-align: center;
            margin-bottom: 4px;
            font-weight: 500;
        }

        .heatmap-cell {
            aspect-ratio: 1;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 600;
            min-height: 40px;
        }

        /* Intensity color scales for workload heatmap */
        .heatmap-cell.intensity-0 {
            background: #20c997;
            color: white;
        }

        .heatmap-cell.intensity-1 {
            background: #28a745;
            color: white;
        }

        .heatmap-cell.intensity-2 {
            background: #ffc107;
            color: white;
        }

        .heatmap-cell.intensity-3 {
            background: #fd7e14;
            color: white;
        }

        .heatmap-cell.intensity-4 {
            background: #dc3545;
            color: white;
        }

        .heatmap-cell.empty {
            background: #f8f9fa;
            border: 1px dashed #dee2e6;
        }

        /* Radar Chart Styles */
        .radar-container {
            position: relative;
            width: 100%;
            max-width: 100%;
            height: 100%;
            min-height: 350px;
            margin: 0 auto;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .radar-svg {
            width: 100%;
            height: 100%;
            min-height: 330px;
        }

        .radar-grid {
            fill: none;
            stroke: #dee2e6;
            stroke-width: 1.5;
        }

        .radar-axis {
            stroke: #adb5bd;
            stroke-width: 1.5;
        }

        .radar-area {
            fill: rgba(96, 187, 233, 0.3);
            stroke: #60BBE9;
            stroke-width: 2.5;
        }

        .radar-target {
            fill: rgba(220, 53, 69, 0.2);
            stroke: #dc3545;
            stroke-width: 2.5;
            stroke-dasharray: 5, 5;
        }

        .radar-label {
            fill: #09243F;
            font-size: 13px;
            font-weight: 600;
            text-anchor: middle;
        }

        /* Alerts */
        .alert {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 14px;
        }

        .alert.danger {
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }

        .alert.success {
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }

        /* Team members */
        .team-member {
            margin-bottom: 18px;
        }

        .team-member-name {
            font-size: 14px;
            font-weight: 600;
            color: #09243F;
            margin-bottom: 6px;
        }

        .team-member-capacity {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 6px;
        }

        .progress-bar {
            width: 100%;
            height: 28px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }

        .progress-fill {
            height: 100%;
            background: #60BBE9;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 13px;
            font-weight: 600;
        }

        .progress-fill.over-capacity {
            background: #dc3545;
        }

        /* Keyboard hint */
        .keyboard-hint {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: rgba(9,36,63,0.9);
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 15px;
            opacity: 0.8;
            z-index: 999;
        }

        /* Hide chat widget */
        .chat-widget,
        #chatSection {
            display: none !important;
        }
    """

def get_tv_scripts():
    """Get JavaScript for TV interface"""

    # Get the original dashboard scripts for charts
    with open('Reports/capacity_dashboard.html', 'r', encoding='utf-8') as f:
        original_html = f.read()

    # Extract script content between <script> tags
    import re
    script_match = re.search(r'<script>(.*?)</script>', original_html, re.DOTALL)
    original_scripts = script_match.group(1) if script_match else ''

    # Add tab navigation and override functions
    tab_navigation = """
    // Override animateProgressRing to work without SVG rings
    function animateProgressRing(elementId, valueId, percentage, isNumber = false) {
        const valueEl = document.getElementById(valueId);
        if (!valueEl) return;

        // Animate the number
        let current = 0;
        const target = isNumber ? percentage : percentage;
        const interval = setInterval(() => {
            current += isNumber ? 1 : 1;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            valueEl.textContent = isNumber ? Math.round(current) : Math.round(current) + '%';
        }, 20);
    }

    // Tab Navigation
    let currentTab = 0;
    const tabs = ['overview', 'projects', 'capacity', 'allocation'];
    const chartsGenerated = {
        overview: false,
        projects: false,
        capacity: false,
        allocation: false
    };

    function showTab(tabName) {
        // Hide all content
        document.querySelectorAll('.tv-content').forEach(content => {
            content.classList.remove('active');
        });

        // Deactivate all tabs
        document.querySelectorAll('.tv-tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected content and activate tab
        const content = document.getElementById(tabName + '-content');
        const tab = document.getElementById(tabName + '-tab');

        if (content) content.classList.add('active');
        if (tab) tab.classList.add('active');

        currentTab = tabs.indexOf(tabName);

        // Generate charts only once when tab becomes visible
        setTimeout(() => {
            if (tabName === 'overview' && !chartsGenerated.overview) {
                console.log('Generating Overview charts...');
                chartsGenerated.overview = true;
            }

            if (tabName === 'projects' && !chartsGenerated.projects) {
                console.log('Generating Projects charts...');
                if (typeof generateTimeline === 'function') {
                    try {
                        generateTimeline();
                        console.log('Timeline generated successfully');
                        const timelineEl = document.getElementById('projectTimeline');
                        if (timelineEl) {
                            console.log('Timeline HTML:', timelineEl.innerHTML.substring(0, 200));
                        }
                    } catch (e) {
                        console.error('Error generating timeline:', e);
                    }
                }
                if (typeof generateRadarChart === 'function') {
                    try {
                        generateRadarChart();
                        console.log('Radar chart generated successfully');
                    } catch (e) {
                        console.error('Error generating radar chart:', e);
                    }
                }
                chartsGenerated.projects = true;
            }

            if (tabName === 'capacity' && !chartsGenerated.capacity) {
                console.log('Generating Capacity charts...');
                if (typeof generateVelocityChart === 'function') {
                    generateVelocityChart();
                    console.log('Velocity chart generated');
                }
                chartsGenerated.capacity = true;
            }

            if (tabName === 'allocation' && !chartsGenerated.allocation) {
                console.log('Generating Allocation charts...');
                if (typeof generateRadarChart === 'function') {
                    try {
                        generateRadarChart();
                        console.log('Allocation radar chart generated');
                    } catch (e) {
                        console.error('Error generating allocation radar chart:', e);
                    }
                }
                chartsGenerated.allocation = true;
            }

            // Trigger resize to help charts adjust
            window.dispatchEvent(new Event('resize'));
        }, 150);
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'Right') {
            currentTab = (currentTab + 1) % tabs.length;
            showTab(tabs[currentTab]);
        } else if (e.key === 'ArrowLeft' || e.key === 'Left') {
            currentTab = (currentTab - 1 + tabs.length) % tabs.length;
            showTab(tabs[currentTab]);
        }
    });

    // Initialize on page load
    window.addEventListener('DOMContentLoaded', () => {
        console.log('Page loaded, initializing Overview tab...');
        // Start with Overview tab (already active by default)
        showTab('overview');
    });
    """

    return original_scripts + '\n' + tab_navigation

def main():
    print("Generating Tabbed TV Dashboard...")

    # Read data
    data = read_reports()

    # Generate regular dashboard first
    generate_html_dashboard(data)

    # Read the generated HTML
    with open('Reports/capacity_dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Transform to tabbed interface
    tabbed_html = create_tabbed_tv_dashboard(html)

    # Write TV-optimized tabbed version
    output_file = 'Reports/capacity_dashboard_tv.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tabbed_html)

    print(f"✅ Tabbed TV Dashboard: {output_file}")
    print("📺 Features:")
    print("   - 4 tabs: Overview, Projects, Capacity, Allocation")
    print("   - Use arrow keys ← → to navigate")
    print("   - Click tabs to switch pages")
    print("   - Optimized for 85\" 4K TV viewing")

if __name__ == '__main__':
    main()
