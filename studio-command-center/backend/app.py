"""
Studio Command Center - Backend API
Serves real-time Asana data for the interactive dashboard
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
from datetime import datetime

# Add parent directory to path to import from StudioProcesses
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('/Users/comstudio/Scripts/StudioProcesses')

# Import the existing data collection functions
from generate_dashboard import read_reports

app = Flask(__name__, static_folder='../frontend/dist')
CORS(app)  # Enable CORS for local development

# Cache data for performance
cache = {
    'data': None,
    'last_updated': None,
    'cache_duration': 300  # 5 minutes
}


def get_fresh_data():
    """Get fresh data from Asana or return cached data if recent"""
    now = datetime.now()

    # Return cached data if it's recent
    if cache['data'] and cache['last_updated']:
        elapsed = (now - cache['last_updated']).total_seconds()
        if elapsed < cache['cache_duration']:
            return cache['data']

    # Fetch fresh data
    print(f"📊 Fetching fresh data from Asana at {now.strftime('%H:%M:%S')}")
    data = read_reports()

    # Update cache
    cache['data'] = data
    cache['last_updated'] = now

    return data


@app.route('/api/status')
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Studio Command Center API',
        'timestamp': datetime.now().isoformat(),
        'cache_age': (datetime.now() - cache['last_updated']).total_seconds() if cache['last_updated'] else None
    })


@app.route('/api/refresh')
def refresh():
    """Force refresh data from Asana"""
    cache['data'] = None
    cache['last_updated'] = None
    data = get_fresh_data()

    return jsonify({
        'status': 'refreshed',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/dashboard')
def dashboard():
    """Get all dashboard data"""
    data = get_fresh_data()

    # Convert datetime objects to ISO strings for JSON serialization
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    # Prepare response
    response = {
        'timestamp': datetime.now().isoformat(),
        'cache_age': (datetime.now() - cache['last_updated']).total_seconds() if cache['last_updated'] else 0,

        # Summary metrics
        'metrics': {
            'total_tasks': data.get('active_task_count', 0),
            'at_risk_count': len(data.get('at_risk_tasks', [])),
            'upcoming_shoots': len(data.get('upcoming_shoots', [])),
            'upcoming_deadlines': len(data.get('upcoming_deadlines', [])),
        },

        # Team capacity
        'team_capacity': data.get('team_capacity', []),

        # At-risk tasks
        'at_risk_tasks': data.get('at_risk_tasks', [])[:20],  # Limit to 20

        # Upcoming shoots
        'upcoming_shoots': [
            {
                'name': s['name'],
                'datetime': s['datetime'].isoformat() if hasattr(s['datetime'], 'isoformat') else str(s['datetime']),
                'project': s.get('project', 'Unknown'),
                'gid': s.get('gid'),
                'start_on': s['start_on'].isoformat() if s.get('start_on') and hasattr(s['start_on'], 'isoformat') else None,
                'due_on': s['due_on'].isoformat() if s.get('due_on') and hasattr(s['due_on'], 'isoformat') else None,
            }
            for s in data.get('upcoming_shoots', [])[:10]
        ],

        # Upcoming deadlines
        'upcoming_deadlines': [
            {
                'name': d['name'],
                'due_date': d['due_date'].isoformat() if hasattr(d['due_date'], 'isoformat') else str(d['due_date']),
                'days_until': d.get('days_until', 0),
                'project': d.get('project', 'Unknown'),
                'gid': d.get('gid'),
                'start_on': d['start_on'].isoformat() if d.get('start_on') and hasattr(d['start_on'], 'isoformat') else None,
            }
            for d in data.get('upcoming_deadlines', [])[:10]
        ],

        # Category data
        'categories': data.get('category_data', []),

        # Delivery metrics
        'delivery_metrics': data.get('delivery_metrics', {}),

        # External projects
        'external_projects': data.get('external_projects', []),
    }

    return jsonify(response)


@app.route('/api/team')
def team():
    """Get team capacity data"""
    data = get_fresh_data()

    team_data = []
    for member in data.get('team_capacity', []):
        utilization = (member['current'] / member['max'] * 100) if member['max'] > 0 else 0
        team_data.append({
            'name': member['name'],
            'current': member['current'],
            'max': member['max'],
            'utilization': round(utilization, 1),
            'status': 'overloaded' if utilization > 100 else 'high' if utilization > 80 else 'normal'
        })

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'team': team_data
    })


@app.route('/api/at-risk')
def at_risk():
    """Get at-risk tasks"""
    data = get_fresh_data()

    tasks = []
    for task in data.get('at_risk_tasks', [])[:20]:
        tasks.append({
            'name': task['name'],
            'project': task.get('project', 'Unknown'),
            'assignee': task.get('assignee', 'Unassigned'),
            'videographer': task.get('videographer'),
            'due_on': task.get('due_on'),
            'risks': task.get('risks', [])
        })

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'count': len(tasks),
        'tasks': tasks
    })


# Serve React app in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the React frontend"""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    print("=" * 60)
    print("🎬 Studio Command Center API Starting...")
    print("=" * 60)
    print(f"📡 API will be available at: http://localhost:5001")
    print(f"📊 Dashboard endpoint: http://localhost:5001/api/dashboard")
    print(f"💚 Health check: http://localhost:5001/api/status")
    print("=" * 60)
    print()

    # Run the app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
