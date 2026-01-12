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
    forecast_cards = []

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

        # Projects: Upcoming shoots, upcoming deadlines, project timeline
        elif 'Upcoming Shoot' in heading_text:
            project_cards.append(str(card))
        elif 'Upcoming Project Deadline' in heading_text:
            project_cards.append(str(card))
        elif heading_text == 'Project Timeline':
            project_cards.append(str(card))
        elif heading_text == 'Workload Balance':
            # Add to Allocation tab only
            card_html = str(card).replace('class="card full-width"', 'class="card"')
            allocation_cards.append(card_html)

        # Forecast: 6-month timeline, historical capacity utilization, forecasted projects (check first before capacity!)
        elif '6-Month Capacity' in heading_text or '6 Month' in heading_text:
            forecast_cards.append(str(card))
        elif heading_text == '📈 Historical Capacity Utilization':
            forecast_cards.append(str(card))
        elif 'Forecasted Projects' in heading_text:
            forecast_cards.append(str(card))

        # Capacity: Team capacity, velocity, 10-day heatmap, capacity utilization
        elif heading_text == 'Team Capacity':
            capacity_cards.append(str(card))
        elif 'Team Velocity' in heading_text or 'Velocity Trend' in heading_text:
            capacity_cards.append(str(card))
        elif 'Workload Heat Map' in heading_text:
            capacity_cards.append(str(card))
        elif 'Capacity Utilization' in heading_text:
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
    # Order: Team Capacity (full width), Velocity, Heatmap, 30-day utilization
    capacity_content = '<div class="grid">'

    # Find and categorize capacity cards
    team_capacity_card = None
    velocity_card = None
    heatmap_card = None
    utilization_30_card = None

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

    # Add in desired order
    if team_capacity_card:
        capacity_content += team_capacity_card
    if velocity_card:
        capacity_content += velocity_card
    if heatmap_card:
        capacity_content += heatmap_card
    if utilization_30_card:
        capacity_content += utilization_30_card

    capacity_content += '</div>'

    # Forecast content - 6-month timeline and historical capacity
    forecast_content = '<div class="grid">' + ''.join(forecast_cards) + '</div>'

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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&display=swap" rel="stylesheet">
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
        <button class="tv-tab" id="forecast-tab" onclick="showTab('forecast')">
            🔮 Forecast
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
        <h1 class="tab-title">Team Capacity</h1>
        {capacity_content}
    </div>

    <div class="tv-content" id="forecast-content">
        <h1 class="tab-title">Capacity Forecast</h1>
        {forecast_content}
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
            list-style: none !important;
            list-style-type: none !important;
        }

        *::before,
        *::after,
        *::marker {
            list-style: none !important;
            list-style-type: none !important;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            overflow: hidden;
        }

        /* Emoji rendering fix */
        button, .timeline-project-name, h1, h2 {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
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
            padding: 28px 24px;
            color: rgba(255,255,255,0.7);
            font-size: 32px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            border: none;
            background: transparent;
            border-bottom: 6px solid transparent;
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
            padding: 110px 40px 30px 40px;
            height: 100vh;
            overflow: hidden;
            box-sizing: border-box;
        }

        .tv-content.active {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .tab-title {
            color: #09243F;
            font-size: clamp(28px, 3vw, 42px);
            margin-bottom: 1.2vh;
            padding-bottom: 0.8vh;
            border-bottom: 3px solid #60BBE9;
            flex-shrink: 0;
            font-weight: 700;
        }

        /* Grid layout - 2 columns for optimal readability */
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5vh 2vw;
            flex: 1;
            overflow: hidden;
            align-content: start;
            grid-auto-rows: auto;
        }

        /* Card styling - no scrolling, auto height */
        .card {
            background: white;
            padding: 1vh 1.5vw;
            border-radius: 12px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.12);
            border: 2px solid #e9ecef;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: auto;
            min-height: 0;
        }

        /* Card content area that can shrink */
        .card > div:not(.card h2) {
            flex: 1;
            min-height: 0;
            overflow: hidden;
        }

        .card h2 {
            color: #09243F;
            font-size: clamp(18px, 2.2vw, 32px);
            margin-bottom: 0.8vh;
            font-weight: 700;
            border-bottom: 2px solid #60BBE9;
            padding-bottom: 0.5vh;
            flex-shrink: 0;
        }

        .card h3 {
            font-size: clamp(14px, 1.6vw, 24px);
            color: #09243F;
            margin: 0.8vh 0;
            font-weight: 600;
        }

        .card p {
            font-size: clamp(12px, 1.4vw, 20px);
            line-height: 1.3;
            margin: 0.5vh 0;
        }

        .full-width {
            grid-column: 1 / -1;
            overflow: hidden;
        }

        /* Metrics */
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1vh 0;
            border-bottom: 1px solid #dee2e6;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-size: clamp(14px, 1.8vw, 26px);
            color: #6c757d;
            font-weight: 500;
        }

        .metric-value {
            font-size: clamp(22px, 3vw, 42px);
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
            gap: 1.5vh 1.5vw;
            margin: 1vh 0;
            padding: 0.8vh 0;
        }

        .progress-ring {
            position: relative;
            width: clamp(90px, 10vw, 120px);
            height: clamp(90px, 10vw, 120px);
            text-align: center;
        }

        .progress-ring-svg {
            transform: rotate(-90deg);
        }

        .progress-ring-circle {
            fill: none;
            stroke-width: 10;
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
            width: 100%;
        }

        .progress-ring svg {
            width: 100% !important;
            height: 100% !important;
        }

        .progress-ring-value {
            font-size: clamp(14px, 1.5vw, 20px);
            font-weight: 700;
            color: #09243F;
            display: block;
            line-height: 1;
        }

        .progress-ring-label {
            font-size: clamp(8px, 0.9vw, 12px);
            color: #6c757d;
            display: block;
            margin-top: 4px;
            line-height: 1.1;
        }

        /* Charts */
        .chart-container {
            position: relative;
            height: clamp(180px, 20vh, 280px);
            margin-top: 0.8vh;
            overflow: hidden;
        }

        /* Forecast tab - single column layout with larger cards */
        #forecast-content .grid {
            grid-template-columns: 1fr !important;
            align-content: stretch !important;
            grid-auto-rows: 1fr !important;
        }

        /* Larger charts for Forecast tab (fewer cards, more vertical space) */
        #forecast-content .card {
            height: auto !important;
            min-height: 42vh !important;
            max-height: none !important;
            padding: 1vh 1.5vw !important;
            display: flex !important;
            flex-direction: column !important;
        }

        /* Reduce subtitle margins on forecast tab */
        #forecast-content .card h2 {
            margin-bottom: 0.3vh !important;
            padding-bottom: 0.3vh !important;
            flex-shrink: 0 !important;
        }

        #forecast-content .card p,
        #forecast-content .card > div[style*="font-size: 12px; color"] {
            margin-bottom: 0.3vh !important;
            margin-top: 0.2vh !important;
            flex-shrink: 0 !important;
        }

        /* All direct children divs of cards should flex */
        #forecast-content .card > div {
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        /* Month header row for 6-month timeline - don't let it grow */
        #forecast-content .card > div > div[style*="display: flex; margin-bottom"] {
            flex: 0 0 auto !important;
            margin-bottom: 0.5vh !important;
        }

        /* Timeline bars container - let it fill remaining space */
        #forecast-content .card > div > div[style*="display: flex; gap: 3px; height"] {
            flex: 1 !important;
            height: auto !important;
            min-height: 0 !important;
            align-items: stretch !important;
        }

        /* Individual timeline bars */
        #forecast-content .card > div > div[style*="display: flex; gap: 3px; height"] > div {
            height: 100% !important;
        }

        /* Make chart containers fill available space */
        #forecast-content .chart-container {
            flex: 1 !important;
            height: auto !important;
            min-height: 0 !important;
            display: flex !important;
            flex-direction: column !important;
        }

        /* Historical capacity chart canvas - fill container */
        #forecast-content .chart-container canvas {
            flex: 1 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 0 !important;
            max-height: none !important;
        }

        canvas {
            max-height: 100% !important;
            width: 100% !important;
        }

        /* Timeline */
        .timeline-container {
            margin: 1vh 0;
            overflow: hidden;
            flex: 1;
            list-style: none !important;
            position: relative;
            padding-left: 0 !important;
            min-height: 0;
        }

        .timeline-container::before {
            content: '';
            position: absolute;
            left: 25%;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #09243F;
            z-index: 10;
        }

        .timeline-container *,
        .timeline-container *::before,
        .timeline-container *::after {
            list-style: none !important;
            list-style-type: none !important;
        }

        .timeline-header {
            display: flex;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #dee2e6;
        }

        .timeline-project-col {
            width: 25%;
            font-weight: 600;
            color: #09243F;
            font-size: clamp(12px, 1.5vw, 22px);
            padding-right: 0.8vw;
            margin-right: 0.8vw;
            flex-shrink: 0;
        }

        .timeline-dates {
            display: flex;
            flex: 1;
        }

        .timeline-date {
            flex: 1;
            text-align: center;
            font-size: clamp(11px, 1.3vw, 20px);
            color: #6c757d;
            font-weight: 500;
        }

        .timeline-row {
            display: flex;
            align-items: center;
            margin-bottom: 0.8vh;
            min-height: 2.5vh;
            list-style: none !important;
            list-style-type: none !important;
        }

        .timeline-row::before,
        .timeline-row::after,
        .timeline-row::marker {
            display: none !important;
            content: none !important;
        }

        .timeline-project-name {
            width: 25%;
            font-size: clamp(12px, 1.5vw, 22px);
            color: #09243F;
            padding-right: 0.8vw;
            font-weight: 500;
            margin-right: 0.8vw;
            flex-shrink: 0;
            line-height: 1.2;
            overflow: hidden;
            word-wrap: break-word;
        }

        .timeline-project-name::before,
        .timeline-project-name::after,
        .timeline-project-name::marker {
            display: none !important;
            content: '' !important;
        }

        .timeline-bars {
            display: flex;
            flex: 1;
            position: relative;
            height: 2.5vh;
            min-height: 24px;
        }

        .timeline-bar {
            position: absolute;
            height: 2vh;
            min-height: 20px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: clamp(10px, 1.1vw, 16px);
            font-weight: 600;
            padding: 0 0.4vw;
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
            font-size: clamp(14px, 1.5vw, 20px);
            color: #6c757d;
            padding: 0.8vh 1.2vw;
            text-align: right;
            font-weight: 600;
        }

        .heatmap-date {
            font-size: clamp(13px, 1.4vw, 18px);
            color: #6c757d;
            text-align: center;
            margin-bottom: 0.5vh;
            font-weight: 500;
        }

        .heatmap-cell {
            aspect-ratio: 1;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: clamp(13px, 1.4vw, 18px);
            font-weight: 600;
            min-height: clamp(40px, 5vh, 60px);
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
            min-height: clamp(250px, 30vh, 400px);
            margin: 0 auto;
            padding: 0.8vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .radar-svg {
            width: 100%;
            height: 100%;
            min-height: clamp(230px, 28vh, 380px);
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
            font-size: clamp(14px, 1.6vw, 22px);
            font-weight: 600;
            text-anchor: middle;
        }

        /* Alerts */
        .alert {
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 1.5vh 1.5vw;
            border-radius: 6px;
            margin-bottom: 1vh;
            font-size: clamp(14px, 1.6vw, 22px);
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
            margin-bottom: 1vh;
        }

        .team-member-name {
            font-size: clamp(13px, 1.6vw, 23px);
            font-weight: 600;
            color: #09243F;
            margin-bottom: 0.3vh;
        }

        .team-member-capacity {
            font-size: clamp(11px, 1.4vw, 20px);
            color: #6c757d;
            margin-bottom: 0.3vh;
        }

        .progress-bar {
            width: 100%;
            height: 2.5vh;
            min-height: 26px;
            background: #e9ecef;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 0.5vh;
        }

        .progress-fill {
            height: 100%;
            background: #60BBE9;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: clamp(11px, 1.4vw, 20px);
            font-weight: 600;
        }

        .progress-fill.over-capacity {
            background: #dc3545;
        }

        /* Keyboard hint */
        .keyboard-hint {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(9,36,63,0.9);
            color: white;
            padding: 18px 32px;
            border-radius: 8px;
            font-size: 26px;
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
    const tabs = ['overview', 'projects', 'capacity', 'forecast', 'allocation'];
    const chartsGenerated = {
        overview: false,
        projects: false,
        capacity: false,
        forecast: false,
        allocation: false
    };

    // Auto-cycle state management
    let autoCycleInterval = null;
    let autoResumeTimeout = null;
    let isPaused = false;

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

            if (tabName === 'forecast' && !chartsGenerated.forecast) {
                console.log('Generating Forecast charts...');
                // Forecast charts are typically rendered from the original dashboard
                // No additional generation needed - charts auto-render
                chartsGenerated.forecast = true;
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

    // Start auto-cycling
    function startAutoCycle() {
        if (autoCycleInterval) {
            clearInterval(autoCycleInterval);
        }
        isPaused = false;
        autoCycleInterval = setInterval(() => {
            currentTab = (currentTab + 1) % tabs.length;
            showTab(tabs[currentTab]);
            console.log('Auto-cycling to tab:', tabs[currentTab]);
        }, 45000); // 45 seconds
        console.log('Auto-cycle started');
    }

    // Stop auto-cycling
    function stopAutoCycle() {
        if (autoCycleInterval) {
            clearInterval(autoCycleInterval);
            autoCycleInterval = null;
        }
        isPaused = true;
        console.log('Auto-cycle paused');
    }

    // Toggle pause/resume
    function togglePause() {
        if (isPaused) {
            // Resume cycling
            if (autoResumeTimeout) {
                clearTimeout(autoResumeTimeout);
                autoResumeTimeout = null;
            }
            startAutoCycle();
        } else {
            // Pause cycling
            stopAutoCycle();
            // Set auto-resume after 30 minutes
            autoResumeTimeout = setTimeout(() => {
                console.log('Auto-resuming after 30 minutes of inactivity');
                startAutoCycle();
            }, 30 * 60 * 1000); // 30 minutes
        }
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'Right') {
            currentTab = (currentTab + 1) % tabs.length;
            showTab(tabs[currentTab]);
        } else if (e.key === 'ArrowLeft' || e.key === 'Left') {
            currentTab = (currentTab - 1 + tabs.length) % tabs.length;
            showTab(tabs[currentTab]);
        } else if (e.key === ' ' || e.code === 'Space') {
            e.preventDefault(); // Prevent page scroll
            togglePause();
        }
    });

    // Initialize on page load
    window.addEventListener('DOMContentLoaded', () => {
        console.log('Page loaded, initializing Overview tab...');
        // Start with Overview tab (already active by default)
        showTab('overview');

        // Start auto-cycling
        startAutoCycle();
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
    print("   - 5 tabs: Overview, Projects, Capacity, Forecast, Allocation")
    print("   - Auto-cycles through tabs every 45 seconds")
    print("   - Press SPACEBAR to pause/resume auto-cycling")
    print("   - Auto-resumes after 30 minutes if paused")
    print("   - Use arrow keys ← → to navigate manually")
    print("   - Click tabs to switch pages")
    print("   - Optimized for 85\" 4K TV viewing")

if __name__ == '__main__':
    main()
