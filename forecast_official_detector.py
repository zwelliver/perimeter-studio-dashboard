#!/usr/bin/env python3
"""
Forecast Official Content Detector
Detects when official content (that matches forecast tasks) gets submitted directly to preproduction
and automatically marks corresponding forecast tasks as complete.

This catches cases where the standard forecast workflow is bypassed (e.g., content directly added to preproduction).

Features:
1. Monitors preproduction for new tasks that match forecast projects
2. Uses fuzzy matching to identify forecast tasks that should be completed
3. Auto-completes forecast tasks when official content is found
4. Handles series-based content (e.g., "DD Season 1" forecast → multiple DD episodes in preproduction)
5. Logs all matches and completions

Runs every 30 minutes via cron (offset from main forecast automation by 15 minutes).
"""

import os
import sys
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from difflib import SequenceMatcher
import re

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forecast_official_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Asana configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

# Project GIDs
FORECAST_PROJECT_GID = '1212059678473189'
PREPRODUCTION_PROJECT_GID = '1208336083003480'
PRODUCTION_PROJECT_GID = '1209597979075357'
POST_PRODUCTION_PROJECT_GID = '1209581743268502'

# Content matching patterns for different types
CONTENT_PATTERNS = {
    'digging_deeper': {
        'forecast_patterns': [r'digging deeper.*season\s*(\d+)', r'dd.*season\s*(\d+)', r'dd\s*(\d+)'],
        'official_patterns': [r'dd\s+into\s+\w+', r'digging deeper.*ep\.*\s*\d+'],
        'match_threshold': 0.6
    },
    'sermon_series': {
        'forecast_patterns': [r'(\w+)\s*series', r'(\w+)\s*sermon', r'(\w+)\s*teaching'],
        'official_patterns': [r'(\w+).*sermon', r'(\w+).*message', r'(\w+).*teaching'],
        'match_threshold': 0.7
    },
    'event_content': {
        'forecast_patterns': [r'(\w+)\s*event', r'(\w+)\s*conference', r'(\w+)\s*retreat'],
        'official_patterns': [r'(\w+).*promo', r'(\w+).*video', r'(\w+).*recap'],
        'match_threshold': 0.8
    }
}

# State file to track processed tasks
STATE_FILE = 'forecast_detector_processed.txt'


def load_processed_tasks():
    """Load list of already processed preproduction task IDs"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_processed_task(task_id):
    """Save a processed task ID to avoid reprocessing"""
    with open(STATE_FILE, 'a') as f:
        f.write(f"{task_id}\n")


def fetch_forecast_tasks():
    """Fetch incomplete tasks from Forecast project"""
    url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}/tasks"
    params = {
        "opt_fields": "gid,name,notes,due_on,completed,custom_fields"
    }

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']
        return [t for t in tasks if not t.get('completed', False)]
    except Exception as e:
        logger.error(f"Error fetching forecast tasks: {e}")
        return []


def fetch_recent_preproduction_tasks():
    """Fetch tasks from preproduction"""
    url = f"https://app.asana.com/api/1.0/projects/{PREPRODUCTION_PROJECT_GID}/tasks"
    params = {
        "opt_fields": "gid,name,notes,due_on,created_at,completed,custom_fields"
    }

    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']

        # Return all tasks - we'll filter by processed state instead of date
        return tasks
    except Exception as e:
        logger.error(f"Error fetching preproduction tasks: {e}")
        return []


def extract_content_info(task_name):
    """Extract content type and key info from task name"""
    name_lower = task_name.lower()

    # Check each content pattern
    for content_type, patterns in CONTENT_PATTERNS.items():
        for pattern in patterns['forecast_patterns'] + patterns['official_patterns']:
            match = re.search(pattern, name_lower)
            if match:
                return {
                    'type': content_type,
                    'key_info': match.groups() if match.groups() else [match.group()],
                    'base_name': re.sub(r'\s*(ep\.*\s*\d+|episode\s*\d+|part\s*\d+).*$', '', name_lower).strip()
                }

    # Fallback: extract base name for generic matching
    base_name = re.sub(r'\s*(ep\.*\s*\d+|episode\s*\d+|part\s*\d+).*$', '', name_lower).strip()
    return {
        'type': 'generic',
        'key_info': [],
        'base_name': base_name
    }


def calculate_match_score(forecast_task, preproduction_task):
    """Calculate similarity score between forecast and preproduction tasks"""
    forecast_info = extract_content_info(forecast_task['name'])
    preproduction_info = extract_content_info(preproduction_task['name'])

    # Type-specific matching
    if forecast_info['type'] == preproduction_info['type'] and forecast_info['type'] != 'generic':
        content_type = forecast_info['type']
        threshold = CONTENT_PATTERNS[content_type]['match_threshold']

        # Compare base names
        base_similarity = SequenceMatcher(None, forecast_info['base_name'], preproduction_info['base_name']).ratio()

        # Bonus for matching key info (season numbers, series names, etc.)
        key_bonus = 0
        if forecast_info['key_info'] and preproduction_info['key_info']:
            for f_key in forecast_info['key_info']:
                for p_key in preproduction_info['key_info']:
                    if str(f_key).lower() == str(p_key).lower():
                        key_bonus = 0.3
                        break

        return min(base_similarity + key_bonus, 1.0), threshold

    # Generic name similarity
    name_similarity = SequenceMatcher(None, forecast_task['name'].lower(), preproduction_task['name'].lower()).ratio()
    return name_similarity, 0.8  # Higher threshold for generic matching


def find_matching_forecast_tasks(preproduction_task, forecast_tasks):
    """Find forecast tasks that match a preproduction task"""
    matches = []

    for forecast_task in forecast_tasks:
        score, threshold = calculate_match_score(forecast_task, preproduction_task)

        if score >= threshold:
            matches.append({
                'forecast_task': forecast_task,
                'score': score,
                'confidence': 'high' if score >= 0.9 else 'medium'
            })

    # Sort by score descending
    return sorted(matches, key=lambda x: x['score'], reverse=True)


def complete_forecast_task(task_id, preproduction_task_name, confidence_score):
    """Mark a forecast task as complete with explanatory comment"""
    try:
        # Complete the task
        complete_response = requests.put(
            f"https://app.asana.com/api/1.0/tasks/{task_id}",
            headers=ASANA_HEADERS,
            json={'data': {'completed': True}}
        )
        complete_response.raise_for_status()

        # Add completion comment
        comment_text = (f"🎯 Auto-completed: Official content detected in preproduction.\n\n"
                       f"Matching task: \"{preproduction_task_name}\"\n"
                       f"Match confidence: {confidence_score:.1%}\n\n"
                       f"Completed by forecast official detector at {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        comment_response = requests.post(
            f"https://app.asana.com/api/1.0/tasks/{task_id}/stories",
            headers=ASANA_HEADERS,
            json={'data': {'text': comment_text}}
        )
        comment_response.raise_for_status()

        return True

    except Exception as e:
        logger.error(f"Error completing forecast task {task_id}: {e}")
        return False


def main():
    """Main detection and completion logic"""
    logger.info("🔍 Starting forecast official content detection...")

    # Load processed tasks to avoid duplicates
    processed_tasks = load_processed_tasks()

    # Fetch data
    forecast_tasks = fetch_forecast_tasks()
    preproduction_tasks = fetch_recent_preproduction_tasks()

    logger.info(f"Found {len(forecast_tasks)} incomplete forecast tasks")
    logger.info(f"Found {len(preproduction_tasks)} recent preproduction tasks")

    completions_made = 0

    # Check each recent preproduction task
    for prep_task in preproduction_tasks:
        task_id = prep_task['gid']

        # Skip if already processed
        if task_id in processed_tasks:
            continue

        # Find matching forecast tasks
        matches = find_matching_forecast_tasks(prep_task, forecast_tasks)

        if matches:
            best_match = matches[0]
            forecast_task = best_match['forecast_task']
            confidence = best_match['score']

            logger.info(f"📋 Match found:")
            logger.info(f"  Preproduction: \"{prep_task['name']}\"")
            logger.info(f"  Forecast: \"{forecast_task['name']}\" (confidence: {confidence:.1%})")

            # Auto-complete if high confidence, or log for manual review
            if confidence >= 0.9:  # High confidence threshold (90% to prevent false positives)
                if complete_forecast_task(forecast_task['gid'], prep_task['name'], confidence):
                    logger.info(f"✅ Auto-completed forecast task: {forecast_task['name']}")
                    completions_made += 1
                else:
                    logger.error(f"❌ Failed to complete forecast task: {forecast_task['name']}")
            else:
                logger.info(f"⚠️ Medium confidence match - manual review recommended")
                logger.info(f"   Add comment to forecast task {forecast_task['gid']} about potential match")

        # Mark as processed
        save_processed_task(task_id)

    logger.info(f"🏁 Detection complete. Made {completions_made} automatic completions.")


if __name__ == "__main__":
    main()