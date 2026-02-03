#!/usr/bin/env python3
"""
Forecast to Official Request Matcher

Automatically detects when an official video request is submitted that matches
a previously forecasted project, and archives/deletes the forecast task.

Matching Logic:
1. Name similarity (fuzzy matching) - weighted heavily
2. Due date proximity (within 30 days)
3. Ministry/Department match
4. Key stakeholder match

Confidence Levels:
- High (>80%): Auto-delete forecast task
- Medium (50-80%): Add comment asking for confirmation
- Low (<50%): No action taken

Runs every 15-30 minutes via cron, checking for new official requests.
"""

import os
import sys
import requests
import logging
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()

# Configure logging
BASE_DIR = os.path.expanduser("~/Scripts/StudioProcesses")
LOG_FILE = os.path.join(BASE_DIR, "forecast_matcher.log")
PROCESSED_FILE = os.path.join(BASE_DIR, "forecast_matcher_processed.json")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
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
VIDEO_OVERVIEW_PROJECT_GID = '1209792136396083'

# Sections in Video Project Overview that receive new requests
NEW_REQUEST_SECTIONS = [
    '1212821259992499',  # Complete the Video Brief
    '1209792136396084',  # Video Project Requests
    '1209802507784567',  # Preproduction (Video Brief Completed) - for tasks that bypass initial request flow
]

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.50

# Matching weights
WEIGHTS = {
    'name': 0.50,       # Name similarity is most important
    'date': 0.25,       # Due date proximity
    'ministry': 0.15,   # Ministry/department match
    'stakeholder': 0.10 # Stakeholder match
}

# Keywords to extract from notes
MINISTRY_KEYWORDS = [
    'global', 'outreach', 'women', 'men', 'student', 'children', 'kids',
    'generosity', 'frontier', 'discipleship', 'belong', 'life on life',
    'lol', 'camp', 'worship', 'communications', 'comm', 'pastoral'
]


def load_processed_tasks():
    """Load list of already processed official request task IDs"""
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'processed': [], 'matches': []}
    return {'processed': [], 'matches': []}


def save_processed_tasks(data):
    """Save processed task IDs"""
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_forecast_tasks():
    """Fetch all incomplete tasks from Forecast project"""
    url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}/tasks"
    params = {
        "opt_fields": "name,notes,due_on,completed,custom_fields"
    }
    
    try:
        response = requests.get(url, headers=ASANA_HEADERS, params=params)
        response.raise_for_status()
        tasks = response.json()['data']
        return [t for t in tasks if not t.get('completed', False)]
    except Exception as e:
        logger.error(f"Error fetching forecast tasks: {e}")
        return []


def fetch_new_official_requests(processed_ids):
    """Fetch recent official video requests that haven't been processed"""
    all_tasks = []

    # Special handling for different sections
    preproduction_section = '1209802507784567'  # Preproduction (Video Brief Completed)
    from datetime import timezone
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)  # Only check tasks created in last 60 days

    for section_gid in NEW_REQUEST_SECTIONS:
        url = f"https://app.asana.com/api/1.0/sections/{section_gid}/tasks"
        params = {
            "opt_fields": "name,notes,due_on,created_at,completed"
        }

        try:
            response = requests.get(url, headers=ASANA_HEADERS, params=params)
            response.raise_for_status()
            tasks = response.json()['data']

            # Filter to incomplete tasks not already processed
            for task in tasks:
                if task.get('completed', False) or task['gid'] in processed_ids:
                    continue

                # For preproduction section, only check recent tasks (to avoid processing old tasks)
                if section_gid == preproduction_section:
                    try:
                        from datetime import timezone
                        created_str = task.get('created_at', '').replace('Z', '+00:00')
                        if created_str:
                            created_date = datetime.fromisoformat(created_str)
                            if created_date < cutoff_date:
                                continue
                    except Exception as e:
                        logger.debug(f"Date parsing error for task {task['gid']}: {e}")
                        continue

                all_tasks.append(task)

        except Exception as e:
            logger.error(f"Error fetching tasks from section {section_gid}: {e}")

    return all_tasks


def normalize_name(name):
    """Normalize task name for comparison"""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common prefixes/suffixes
    remove_patterns = [
        r'^video[:\s-]*',
        r'video$',
        r'^design[:\s-]*',
        r'testimony$',
        r'testimonial$',
        r'\d{4}',  # Remove years
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*',  # Remove months
    ]
    
    for pattern in remove_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove special characters and extra whitespace
    name = re.sub(r'[^\w\s]', ' ', name)
    name = ' '.join(name.split())
    
    return name.strip()


def calculate_name_similarity(name1, name2):
    """Calculate similarity between two task names"""
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Direct sequence matching
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Also check if key words overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        word_overlap = len(words1 & words2) / max(len(words1), len(words2))
        # Combine both scores, weighting sequence matching higher
        ratio = (ratio * 0.6) + (word_overlap * 0.4)
    
    return ratio


def calculate_date_proximity(date1_str, date2_str):
    """Calculate how close two dates are (1.0 = same date, 0.0 = >60 days apart)"""
    if not date1_str or not date2_str:
        return 0.5  # Neutral if either date is missing
    
    try:
        date1 = datetime.strptime(date1_str, '%Y-%m-%d')
        date2 = datetime.strptime(date2_str, '%Y-%m-%d')
        
        days_apart = abs((date1 - date2).days)
        
        if days_apart == 0:
            return 1.0
        elif days_apart <= 7:
            return 0.9
        elif days_apart <= 14:
            return 0.8
        elif days_apart <= 30:
            return 0.6
        elif days_apart <= 60:
            return 0.3
        else:
            return 0.0
            
    except Exception as e:
        logger.debug(f"Date parsing error: {e}")
        return 0.5


def extract_ministry(notes):
    """Extract ministry/department from task notes"""
    if not notes:
        return set()
    
    notes_lower = notes.lower()
    found = set()
    
    for keyword in MINISTRY_KEYWORDS:
        if keyword in notes_lower:
            found.add(keyword)
    
    # Also look for explicit "Ministry Department:" field
    match = re.search(r'ministry\s*(?:department|or department)?[:\s]+([^\n]+)', notes_lower)
    if match:
        ministry_text = match.group(1).strip()
        for keyword in MINISTRY_KEYWORDS:
            if keyword in ministry_text:
                found.add(keyword)
    
    return found


def extract_stakeholder(notes):
    """Extract key stakeholder names from task notes"""
    if not notes:
        return set()
    
    stakeholders = set()
    
    # Look for stakeholder field
    patterns = [
        r'(?:key\s+)?stakeholder[s]?[:\s]+([^\n]+)',
        r'who\s+are\s+the\s+stakeholders[?]?[:\s]+([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, notes, re.IGNORECASE)
        if match:
            names = match.group(1).strip().lower()
            # Extract individual names (split by comma, /, etc)
            for name in re.split(r'[,/&]', names):
                name = name.strip()
                if name and len(name) > 2:
                    stakeholders.add(name)
    
    return stakeholders


def calculate_ministry_match(notes1, notes2):
    """Calculate ministry/department overlap"""
    ministry1 = extract_ministry(notes1)
    ministry2 = extract_ministry(notes2)
    
    if not ministry1 or not ministry2:
        return 0.5  # Neutral if we can't extract ministry
    
    overlap = len(ministry1 & ministry2)
    total = len(ministry1 | ministry2)
    
    if total == 0:
        return 0.5
    
    return overlap / total


def calculate_stakeholder_match(notes1, notes2):
    """Calculate stakeholder name overlap"""
    stakeholders1 = extract_stakeholder(notes1)
    stakeholders2 = extract_stakeholder(notes2)
    
    if not stakeholders1 or not stakeholders2:
        return 0.5  # Neutral if we can't extract stakeholders
    
    # Check for any overlap in names (partial matching)
    for s1 in stakeholders1:
        for s2 in stakeholders2:
            if s1 in s2 or s2 in s1:
                return 1.0
    
    return 0.0


def calculate_match_confidence(official_task, forecast_task):
    """Calculate overall match confidence between an official request and forecast"""
    
    # Name similarity
    name_score = calculate_name_similarity(
        official_task.get('name', ''),
        forecast_task.get('name', '')
    )
    
    # Date proximity
    date_score = calculate_date_proximity(
        official_task.get('due_on'),
        forecast_task.get('due_on')
    )
    
    # Ministry match
    ministry_score = calculate_ministry_match(
        official_task.get('notes', ''),
        forecast_task.get('notes', '')
    )
    
    # Stakeholder match
    stakeholder_score = calculate_stakeholder_match(
        official_task.get('notes', ''),
        forecast_task.get('notes', '')
    )
    
    # Calculate weighted score
    total_score = (
        name_score * WEIGHTS['name'] +
        date_score * WEIGHTS['date'] +
        ministry_score * WEIGHTS['ministry'] +
        stakeholder_score * WEIGHTS['stakeholder']
    )
    
    return {
        'total': total_score,
        'name': name_score,
        'date': date_score,
        'ministry': ministry_score,
        'stakeholder': stakeholder_score
    }


def find_best_match(official_task, forecast_tasks):
    """Find the best matching forecast task for an official request"""
    best_match = None
    best_score = 0.0
    
    for forecast_task in forecast_tasks:
        scores = calculate_match_confidence(official_task, forecast_task)
        
        if scores['total'] > best_score:
            best_score = scores['total']
            best_match = {
                'forecast_task': forecast_task,
                'scores': scores
            }
    
    return best_match


def delete_forecast_task(task_gid):
    """Delete a forecast task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
    
    try:
        response = requests.delete(url, headers=ASANA_HEADERS)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error deleting task {task_gid}: {e}")
        return False


def add_comment_to_task(task_gid, comment_text):
    """Add a comment to a task"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    payload = {"data": {"text": comment_text}}
    
    try:
        response = requests.post(url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error adding comment to task {task_gid}: {e}")
        return False


def process_match(official_task, match_result, processed_data):
    """Process a match based on confidence level"""
    forecast_task = match_result['forecast_task']
    scores = match_result['scores']
    confidence = scores['total']
    
    official_name = official_task['name']
    forecast_name = forecast_task['name']
    forecast_gid = forecast_task['gid']
    official_gid = official_task['gid']
    
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        # High confidence - auto-delete forecast
        logger.info(f"🎯 HIGH CONFIDENCE MATCH ({confidence:.0%})")
        logger.info(f"   Official: {official_name}")
        logger.info(f"   Forecast: {forecast_name}")
        
        # Add comment to official task noting the match
        comment = (
            f"✅ Auto-matched with forecast task: {forecast_name}\n\n"
            f"Match confidence: {confidence:.0%}\n"
            f"- Name similarity: {scores['name']:.0%}\n"
            f"- Date proximity: {scores['date']:.0%}\n"
            f"- Ministry match: {scores['ministry']:.0%}\n"
            f"- Stakeholder match: {scores['stakeholder']:.0%}\n\n"
            f"The forecast task has been automatically deleted."
        )
        add_comment_to_task(official_gid, comment)
        
        # Delete the forecast task
        if delete_forecast_task(forecast_gid):
            logger.info(f"   ✅ Forecast task deleted")
            processed_data['matches'].append({
                'official_gid': official_gid,
                'forecast_gid': forecast_gid,
                'confidence': confidence,
                'action': 'auto_deleted',
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.error(f"   ❌ Failed to delete forecast task")
            
    elif confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
        # Medium confidence - add comment asking for confirmation
        logger.info(f"🔍 MEDIUM CONFIDENCE MATCH ({confidence:.0%})")
        logger.info(f"   Official: {official_name}")
        logger.info(f"   Forecast: {forecast_name}")
        
        forecast_link = f"https://app.asana.com/0/{FORECAST_PROJECT_GID}/{forecast_gid}"
        
        comment = (
            f"🔍 Possible forecast match detected!\n\n"
            f"This request may match a previously forecasted project:\n"
            f"📋 **{forecast_name}**\n"
            f"🔗 {forecast_link}\n\n"
            f"Match confidence: {confidence:.0%}\n"
            f"- Name similarity: {scores['name']:.0%}\n"
            f"- Date proximity: {scores['date']:.0%}\n"
            f"- Ministry match: {scores['ministry']:.0%}\n"
            f"- Stakeholder match: {scores['stakeholder']:.0%}\n\n"
            f"If this is a match, please delete the forecast task manually."
        )
        add_comment_to_task(official_gid, comment)
        logger.info(f"   📝 Comment added to official task")
        
        processed_data['matches'].append({
            'official_gid': official_gid,
            'forecast_gid': forecast_gid,
            'confidence': confidence,
            'action': 'comment_added',
            'timestamp': datetime.now().isoformat()
        })
        
    else:
        # Low confidence - no match found
        logger.debug(f"No confident match for: {official_name} (best: {confidence:.0%})")


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Forecast to Official Request Matcher - Starting")
    logger.info("=" * 60)
    
    if not ASANA_PAT:
        logger.error("ASANA_PAT_SCORER not found in environment")
        return
    
    # Load processed tasks
    processed_data = load_processed_tasks()
    processed_ids = set(processed_data.get('processed', []))
    
    # Fetch forecast tasks
    forecast_tasks = fetch_forecast_tasks()
    logger.info(f"Found {len(forecast_tasks)} incomplete forecast task(s)")
    
    if not forecast_tasks:
        logger.info("No forecast tasks to match against")
        logger.info("=" * 60)
        return
    
    # Fetch new official requests
    official_tasks = fetch_new_official_requests(processed_ids)
    logger.info(f"Found {len(official_tasks)} new official request(s) to check")
    
    if not official_tasks:
        logger.info("No new official requests to process")
        logger.info("=" * 60)
        return
    
    # Process each official request
    matches_found = 0
    for official_task in official_tasks:
        # Find best matching forecast
        match_result = find_best_match(official_task, forecast_tasks)
        
        if match_result and match_result['scores']['total'] >= MEDIUM_CONFIDENCE_THRESHOLD:
            process_match(official_task, match_result, processed_data)
            matches_found += 1
            
            # Remove matched forecast from list (so we don't match it again)
            forecast_tasks = [
                t for t in forecast_tasks 
                if t['gid'] != match_result['forecast_task']['gid']
            ]
        
        # Mark as processed regardless of match
        processed_data['processed'].append(official_task['gid'])
    
    # Keep only last 500 processed IDs to prevent file bloat
    processed_data['processed'] = processed_data['processed'][-500:]
    
    # Save processed tasks
    save_processed_tasks(processed_data)
    
    logger.info("")
    logger.info(f"✅ Processed {len(official_tasks)} official request(s)")
    logger.info(f"   Matches found: {matches_found}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
