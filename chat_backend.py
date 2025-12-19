#!/usr/bin/env python3
"""
Capacity Dashboard Chat Backend
Provides an API endpoint for the embedded Claude chat widget
Fetches real Asana task data with 60-second caching for fast responses
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from datetime import datetime
import requests
import time

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow requests from GitHub Pages

# Initialize Claude client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Asana configuration
ASANA_PAT = os.getenv('ASANA_PAT_SCORER')
ASANA_HEADERS = {
    'Authorization': f'Bearer {ASANA_PAT}',
    'Content-Type': 'application/json'
}
ASANA_PROJECTS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}
PERCENT_ALLOCATION_FIELD_GID = '1208923995383367'
PRIORITY_FIELD_GID = '1209600375748352'
CATEGORY_FIELD_GID = '1211901611025610'

# Category GID mappings
CATEGORY_GIDS = {
    '1211901611025611': 'Spiritual Formation',
    '1211901611025612': 'Communications',
    '1211901611025613': 'Pastoral/Strategic',
    '1211901611025614': 'Partners',
    '1211901611025615': 'Creative Resources'
}

# Target capacity allocations per category
CATEGORY_TARGETS = {
    'Spiritual Formation': 25,
    'Communications': 30,
    'Creative Resources': 15,
    'Pastoral/Strategic': 20,
    'Partners': 5
}

# Cache for Asana data (60-second TTL)
asana_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 60
}

def fetch_asana_data():
    """Fetch current Asana task data with 60-second caching"""
    current_time = time.time()

    # Check if cache is still valid
    if asana_cache['data'] and (current_time - asana_cache['timestamp']) < asana_cache['ttl']:
        return asana_cache['data']

    # Cache expired or empty, fetch fresh data
    print("📊 Fetching fresh Asana data...")
    all_tasks = []

    for project_name, project_gid in ASANA_PROJECTS.items():
        try:
            response = requests.get(
                f'https://app.asana.com/api/1.0/projects/{project_gid}/tasks',
                headers=ASANA_HEADERS,
                params={
                    'opt_fields': 'gid,name,assignee.name,due_on,completed,custom_fields,priority'
                }
            )

            if response.status_code == 200:
                tasks = response.json().get('data', [])
                for task in tasks:
                    if not task.get('completed', False):  # Only incomplete tasks
                        # Extract percent allocation, priority, and category from custom fields
                        percent_allocation = 0
                        priority = None
                        category = None

                        for field in task.get('custom_fields', []):
                            if field.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                                percent_allocation = field.get('number_value', 0)
                            if field.get('gid') == PRIORITY_FIELD_GID:
                                priority = field.get('number_value')
                            if field.get('gid') == CATEGORY_FIELD_GID:
                                enum_value = field.get('enum_value')
                                if enum_value:
                                    category_gid = enum_value.get('gid')
                                    category = CATEGORY_GIDS.get(category_gid, 'Unknown')

                        all_tasks.append({
                            'name': task.get('name', 'Untitled'),
                            'assignee': task.get('assignee', {}).get('name', 'Unassigned'),
                            'due_on': task.get('due_on'),
                            'percent_allocation': percent_allocation * 100 if percent_allocation else 0,  # Convert to percentage
                            'priority': priority,
                            'category': category,
                            'project': project_name
                        })
        except Exception as e:
            print(f"⚠️ Error fetching {project_name}: {e}")

    # Update cache
    asana_cache['data'] = all_tasks
    asana_cache['timestamp'] = current_time
    print(f"✅ Cached {len(all_tasks)} tasks")

    return all_tasks

def format_tasks_for_prompt(tasks):
    """Format task data into a readable prompt section"""
    if not tasks:
        return "No tasks found.", {}

    # Calculate category utilization
    category_utilization = {}
    for task in tasks:
        category = task.get('category', 'Unknown')
        if category not in category_utilization:
            category_utilization[category] = 0
        category_utilization[category] += task['percent_allocation']

    # Group by assignee
    by_assignee = {}
    for task in tasks:
        assignee = task['assignee']
        if assignee not in by_assignee:
            by_assignee[assignee] = []
        by_assignee[assignee].append(task)

    output = []
    for assignee, assignee_tasks in sorted(by_assignee.items()):
        total_allocation = sum(t['percent_allocation'] for t in assignee_tasks)
        output.append(f"\n**{assignee}** (Total: {total_allocation:.1f}%)")

        # Sort by priority (higher number = higher priority, so descending)
        sorted_tasks = sorted(assignee_tasks, key=lambda t: (t['priority'] if t['priority'] is not None else 0, t['name']), reverse=True)

        for task in sorted_tasks:
            priority_str = f"P{int(task['priority'])}" if task['priority'] is not None else "No Priority"
            due_str = task['due_on'] if task['due_on'] else "No due date"
            category_str = f" [{task['category']}]" if task.get('category') else ""
            output.append(f"  - [{priority_str}]{category_str} {task['name']} ({task['percent_allocation']:.0f}%) - {task['project']} - Due: {due_str}")

    return "\n".join(output), category_utilization

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the dashboard"""
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Fetch current Asana data (cached for 60 seconds)
        tasks = fetch_asana_data()
        tasks_formatted, category_utilization = format_tasks_for_prompt(tasks)

        # Format category utilization comparison
        category_summary = []
        for category in sorted(CATEGORY_TARGETS.keys()):
            target = CATEGORY_TARGETS[category]
            actual = category_utilization.get(category, 0)
            variance = actual - target
            variance_str = f"+{variance:.1f}%" if variance > 0 else f"{variance:.1f}%"
            category_summary.append(f"  - {category}: {actual:.1f}% (Target: {target}%, Variance: {variance_str})")

        category_summary_text = "\n".join(category_summary)

        # Build system prompt with real task data
        system_prompt = f"""You are a helpful assistant for the Perimeter Studio video production team.
You help answer questions about team capacity, workload, project planning, and resource allocation.

## Team Members & Max Capacity:
- Zach Welliver (max capacity: 50%)
- Nick Clark (max capacity: 100%)
- Adriel Abella (max capacity: 100%)
- John Meyer (max capacity: 30%)

## Category Targets vs Actual Utilization:
{category_summary_text}

## Category Definitions:
- **Spiritual Formation (25% target)**: Discipleship/teaching content for primary audience (teaching series, Life on Life)
- **Communications (30% target)**: Inspiring stories and updates (WOV, testimonies, campaign updates, event recaps)
- **Creative Resources (15% target)**: Creative outreach with broad appeal (music videos, Radical Dependence)
- **Pastoral/Strategic (20% target)**: Senior pastor and strategic content (Digging Deeper, Ask the Pastor, Jeff Norris content)
- **Partners (5% target)**: Supporting church plants, nonprofits, and global partners

## Current Incomplete Tasks:
{tasks_formatted}

## Guidelines:
- Priority scale: 12 (highest) to 1 (lowest)
- Be brief and direct - answer in 2-4 sentences max
- Use plain conversational text - no lists, numbers, colons, parentheses, or special characters
- Don't repeat the same information twice (like saying "P5" and "Priority 5")
- Focus on the specific question asked without extra commentary

User is viewing the capacity dashboard and wants to dig deeper into the data."""

        # Call Claude API with task data in prompt
        message = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract only text blocks from response, filtering out tool_use blocks
        response_parts = []
        for block in message.content:
            if block.type == "text":
                response_parts.append(block.text)

        response_text = "\n\n".join(response_parts)

        return jsonify({
            'response': response_text,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Capacity Dashboard Chat Backend...")
    print("📊 Backend will serve on http://localhost:5001")
    print("💬 Dashboard can now use embedded chat!")
    print("💡 Using port 5001 to avoid conflict with macOS AirPlay Receiver")
    app.run(host='127.0.0.1', port=5001, debug=False)
