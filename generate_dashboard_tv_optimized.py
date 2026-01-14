#!/usr/bin/env python3
"""
TV-Optimized Dashboard Generator
Creates a single-screen layout designed for large TV displays
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main dashboard generator
from generate_dashboard import read_reports, generate_html_dashboard

def add_tv_optimization_css(html):
    """Add TV-specific CSS to make everything fit on one screen"""

    # Insert TV-optimized CSS before </style>
    tv_css = """

    /* TV OPTIMIZATION - Scale down approach for 85" 4K display */
    @media screen and (min-width: 1920px) {
        body {
            transform: scale(0.75);
            transform-origin: top left;
            width: 133.33%;
            overflow-x: hidden !important;
        }

        .container {
            max-width: 100% !important;
        }

        /* Fix progress rings scaling */
        .progress-ring {
            transform: scale(1.1) !important;
        }

        .progress-ring-svg {
            width: 140px !important;
            height: 140px !important;
        }

        .progress-ring-text {
            transform: scale(1) !important;
        }

        .progress-ring-value {
            font-size: 26px !important;
            line-height: 1 !important;
        }

        .progress-ring-label {
            font-size: 11px !important;
            margin-top: 6px !important;
        }

        /* Timeline improvements - separate header from bars */
        .timeline-container {
            display: flex !important;
            flex-direction: column !important;
            gap: 15px !important;
        }

        .timeline-header {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            padding-bottom: 12px !important;
            border-bottom: 2px solid #dee2e6 !important;
            margin-bottom: 0 !important;
        }

        .timeline-project-col {
            font-weight: 600 !important;
            color: #09243F !important;
            font-size: 14px !important;
        }

        .timeline-dates {
            display: flex !important;
            gap: 20px !important;
        }

        .timeline-date {
            font-size: 12px !important;
            color: #6c757d !important;
            white-space: nowrap !important;
        }

        .timeline-row {
            display: flex !important;
            align-items: center !important;
            margin-bottom: 10px !important;
            gap: 15px !important;
        }

        .timeline-project-name {
            min-width: 200px !important;
            font-size: 14px !important;
            color: #09243F !important;
            font-weight: 500 !important;
        }

        .timeline-bars {
            flex: 1 !important;
            position: relative !important;
            height: 32px !important;
        }

        /* Hide chat widget for cleaner TV display */
        .chat-widget,
        #chatSection {
            display: none !important;
        }
    }
    """

    html = html.replace('</style>', tv_css + '\n</style>')
    return html

def main():
    print("Generating TV-Optimized Dashboard...")

    # Read data
    data = read_reports()

    # Generate regular dashboard first (writes to capacity_dashboard.html)
    generate_html_dashboard(data)

    # Read the generated HTML
    with open('Reports/capacity_dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Add TV optimizations
    html = add_tv_optimization_css(html)

    # Write TV-optimized version
    output_file = 'Reports/capacity_dashboard_tv.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ TV-Optimized dashboard: {output_file}")
    print("Dashboard fits on one screen at 1920x1080 or higher")

if __name__ == '__main__':
    main()
