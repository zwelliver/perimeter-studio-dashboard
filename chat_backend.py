#!/usr/bin/env python3
"""
Capacity Dashboard Chat Backend
Provides an API endpoint for the embedded Claude chat widget
Uses Claude's direct Asana integration for real-time data access
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow requests from GitHub Pages

# Initialize Claude client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Asana project information
ASANA_PROJECTS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the dashboard"""
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Build system prompt that leverages Claude's Asana access
        system_prompt = f"""You are a helpful assistant for the Perimeter Studio video production team.
You help answer questions about team capacity, workload, project planning, and resource allocation.

IMPORTANT: You have direct access to the Asana account and can query it in real-time to answer questions.

## Key Asana Projects:
- Preproduction: {ASANA_PROJECTS['Preproduction']}
- Production: {ASANA_PROJECTS['Production']}
- Post Production: {ASANA_PROJECTS['Post Production']}
- Forecast: {ASANA_PROJECTS['Forecast']}

## Team Members:
- Zach Welliver (max capacity: 50%)
- Nick Clark (max capacity: 100%)
- Adriel Abella (max capacity: 120%)
- John Meyer (max capacity: 30%)

## Custom Fields:
- "Percent Allocation" field (GID: 1208923995383367) - stores allocation as decimal (0.13 = 13%)
- "Priority" field - 1-12 scale
- "Category" field - grouping for variance tracking

When answering questions:
1. Use your Asana integration to fetch current, real-time data
2. Look at incomplete tasks across all production projects
3. Calculate team utilization by summing Percent Allocation for each assignee
4. Identify at-risk tasks (overdue, due soon without start date, over estimate)
5. Be concise but specific with actual numbers and task names
6. Provide actionable insights and recommendations

User is viewing the capacity dashboard and wants to dig deeper into the data."""

        # Call Claude API - Claude will use Asana integration as needed
        message = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        response_text = message.content[0].text

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
