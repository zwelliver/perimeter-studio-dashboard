import requests
import json
import re
import datetime
import os
import time
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from capacity_alerts import log_alert_to_file, send_email_alert, send_slack_alert
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Load environment variables from .env file in the current directory
load_dotenv(".env")

# Logging setup
BASE_DIR = os.path.expanduser("~/Scripts/StudioProcesses")
LOG_FILE = os.path.join(BASE_DIR, "video_scorer.log")
AUDIT_LOG_FILE = os.path.join(BASE_DIR, "manipulation_audit.log")

# Ensure directories exist
os.makedirs(BASE_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Audit logger for manipulation detection
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler(AUDIT_LOG_FILE)
audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.WARNING)

# Configuration
CONFIG = {
    'DEFAULT_DURATION_DAYS': 30,  # Default project duration when due date is missing
    'GENERATE_REPORTS_ONLY_ON_CHANGES': False,  # Always generate reports to reflect manual changes
    'MAX_CONCURRENT_TASKS': 5,  # Number of tasks to process concurrently
}

# Asana setup
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT}", "Content-Type": "application/json"}

# Internal projects (affect team capacity and get scored)
PROJECT_GIDS = {
    "Preproduction": "1208336083003480",
    "Production": "1209597979075357",
    "Post Production": "1209581743268502",
    "Forecast": "1212059678473189"
}

# External projects (tracking only, do not get scored or affect capacity)
EXTERNAL_PROJECT_GIDS = {
    "Contracted/Outsourced": "1212319598244265"
}

# Team member capacity configuration
TEAM_CAPACITY = {
    "Zach Welliver": {
        "gid": "1205076276256605",
        "capacity": 80,  # 80% capacity
        "projects": ["Preproduction"]
    },
    "Nick Clark": {
        "gid": "1202206953008470",
        "capacity": 100,  # 100% capacity
        "projects": ["Production"]
    },
    "Adriel Abella": {
        "gid": "1208249805795150",
        "capacity": 100,  # 100% capacity
        "projects": ["Post Production"]
    },
    "John Meyer": {
        "gid": "1211292436943049",
        "capacity": 30,  # 30% capacity
        "projects": ["Preproduction", "Production", "Post Production"]  # Can work on any phase
    }
}

# Custom field GID for Percent allocation
PERCENT_ALLOCATION_FIELD_GID = "1208923995383367"

# Custom field GID for Actual Allocation (optional - for tracking actual time spent)
# This field can be populated manually or via time tracking integration
ACTUAL_ALLOCATION_FIELD_GID = "1212060330747288"  # Post Production project

# Claude/Anthropic setup (migrated from Grok xAI - API deprecated Feb 20, 2026)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_ENDPOINT = "https://api.anthropic.com/v1/messages"
CLAUDE_HEADERS = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Fast, capable model for scoring

# Target allocations
TARGETS = {
    'Spiritual Formation': 0.25,
    'Communications': 0.30,
    'Creative Resources': 0.15,
    'Pastoral/Strategic': 0.20,
    'Partners': 0.05
}

# Calculate total team capacity from individual limits (Zach 80% + Nick 100% + Adriel 100% + John 30%)
MAX_CAPACITY = sum(member["capacity"] for member in TEAM_CAPACITY.values())  # 310%

# Phase effort multipliers for allocation calculation
# Post production (editing) requires significantly more time than planning/filming
PHASE_MULTIPLIERS = {
    "Preproduction": 0.8,    # Planning, scripting - lighter effort
    "Production": 1.2,        # Filming, recording - moderate effort
    "Post Production": 2.0    # Editing, revisions - most intensive
}

# Phase weights for heatmap generation (kept for compatibility)
PHASE_WEIGHTS = {
    'Pre': 0.25,
    'Production': 0.25,
    'Post': 0.50
}

# Category enum option GIDs (from your curl)
CATEGORY_OPTION_GIDS = {
    'Spiritual Formation': '1211901611025611',
    'Communications': '1211901611025612',
    'Pastoral/Strategic': '1211901611025613',
    'Partners': '1211901611025614',
    'Creative Resources': '1211901611025615'
}

# Type enum option GIDs (from curl)
TYPE_OPTION_GIDS = {
    'Equipping': '1209581744608310',
    'Enriching': '1209581744608311',
    'Ministry Support': '1209581744608312',
    'Partner Support': '1209581744608313'
}

SYSTEM_PROMPT = """
You are a Video Project Scoring Assistant for Perimeter Church Video Studio. Analyze the provided project details—PRIMARILY the content summary (bullet points) and factual notes—to calculate a Priority Score (Purpose + Audience + Scope, each 1-4, total 3-12), Complexity Rating (1-4), Mapped Category, and Mapped Type. Base scoring SOLELY on objective alignment with the definitions and examples below. Treat self-reported fields (e.g., Purpose/Audience/Scope/Type selections in the form) as SECONDARY: Cross-verify them against the content; if they conflict (e.g., form says 'Ministry Support' but summary describes discipleship teaching), OVERRIDE with the factual content to prevent manipulation or bias. Make reasonable, conservative assumptions if details are sparse, prioritizing definitions over form labels.

- Purpose/Type (intent of video—map to one: Equipping, Enriching, Ministry Support, Partner Support):
  - Equipping - Discipleship content for our church, relevant to the broader Church, or tied to Senior Pastor Jeff Norris. Examples: 'Digging Deeper,' teaching series (e.g., 'God Owns It All'), Strategic Partnerships (RightNow Media, Ron Blue, TGC), Jeff Norris sermon intros or content, Life on Life Missional Discipleship (LOL) videos.
  - Enriching - 'Inviting, Inspiring' stories and opportunities specific to Perimeter, especially seasonal (Holy Week, Easter, Christmas, Advent). Examples: Weekly Opportunity Video (WOV), member testimonies, campaign updates (Forward, Frontier), music videos, seasonal promos, Belong ministry videos.
  - Ministry Support - Initiated by a formal Perimeter ministry to directly support it. Examples: event captures, recaps, highlights, promos, social media reels, ministry profiles for KidsRock, KidsQuest, GloryKids, KidsThrive, Rush, Camp All-American (CAA), Perimeter School, Men's, Women's, Young Adults.
  - Partner Support - Requested by a partner or informal ministry to support them. Examples: church plant, local non-profit, Perimeter Village, global partner/ministry.

- Audience (who it reaches):
  - 4: Church-wide - Relevant to most/all our congregation, often played Sundays, or tied to Senior Pastor Jeff Norris, Outdoor Events (OME), or Belong ministry. Examples: major updates, teaching series, Jeff Norris content, OME promos, Belong initiatives.
  - 3: Community - Represents Perimeter to a broader, external audience. Examples: 'Plan Your Visit' for newcomers, public-facing promos.
  - 2: People Groups - Relevant to key demographics (e.g., men, women, marrieds, youth, students, children, camp families). Examples: videos for KidsRock, KidsQuest, GloryKids, KidsThrive, Rush, Camp All-American (CAA), Perimeter School, Men's, Women's, Young Adults.
  - 1: Ministry Groups - Relevant to specific groups, including partners (e.g., elders, camp staff, Perimeter Village).

- Scope (impact and longevity):
  - 4: High - Evergreen content with broad appeal, usable beyond initial context. Examples: website staples, teaching series (e.g., 'God Owns It All'), long-term Jeff Norris content, LOL discipleship videos.
  - 3: Medium-High - Significant but shorter-term relevance, including seasonal projects (Holy Week, Easter, Christmas, Advent, Christmas Eve). Examples: campaign videos, multi-channel seasonal content.
  - 2: Medium - Event-driven or seasonal with moderate reach. Examples: summer series, event promos for specific ministries.
  - 1: Low - Short-term, limited reach. Examples: one-off event captures, single-use reels.

- Complexity (production effort, 1-12 scale - MUST consider video duration from form):
  - 1-2: Minimal - Simple talking head, <1 min, minimal edits, single take
  - 3-4: Low - Basic graphics, 1-2 min, single shoot, simple B-roll
  - 5-6: Medium-Low - Multiple takes, 2-4 min, moderate graphics, basic effects
  - 7-8: Medium - Multiple shoots, 4-8 min, moderate effects, professional B-roll, interviews/testimonials
  - 9-10: High - Complex edits, 8-15 min, multi-day production, advanced effects, narrative structure
  - 11-12: Very High - Multi-location shoots, 15+ min, extensive post-production, motion graphics, complex workflows

  IMPORTANT: Video duration is a PRIMARY complexity factor. A 10-minute testimonial is significantly more complex than a 2-minute announcement. Check form notes for duration and adjust complexity accordingly.

B-Roll Requirements:
  - Check form notes for mentions of "B-roll", "b-roll", "broll", "B roll", or "additional footage"
  - Videos requiring B-roll capture need additional filming time, locations, and editing
  - Set "broll_required": true if B-roll is mentioned or requested
  - This will apply a 1.5x effort multiplier to the Production phase

Category Mapping Table (use after scoring; override form if mismatch):
| Category | % Allocation | Mapped Priority Elements | Examples |
|----------|--------------|--------------------------|----------|
| Spiritual Formation | 25% | Purpose 4 (Equipping: discipleship/teaching for primary audience); Audience 4 (Churchwide); Scope 3–4 (Medium-High/High, evergreen) | Teaching series (e.g., "God Owns It All"), Life on Life |
| Communications | 30% | Purpose 3 (Enriching: inspiring stories/updates); Audience 4 (Churchwide) or 2 (People Groups); Scope 2–3 (Medium/Medium-High, seasonal/event-driven) | WOV, Testimonies, Campaign updates, Event recaps |
| Creative Resources | 15% | Purpose 3 (Enriching: creative outreach); Audience 3 (Community); Scope 3–4 (Medium-High/High, broad appeal) | Music videos, Radical Dependence |
| Pastoral/Strategic | 20% | Purpose 4 (Equipping: senior pastor/strategic ties); Audience 4 (Churchwide); Scope 4 (High, evergreen) | Digging Deeper, Ask the Pastor, Jeff Norris content |
| Partners | 5% | Purpose 1 (Partner Support); Audience 1 (Ministry Groups) or 3 (Community); Scope 1–2 (Low/Medium, short-term) | Church plants, CO nonprofits, Global partners |

Prioritize Jeff Norris as highest-value (e.g., senior pastor-featured content elevates to Purpose 4); treat OME and Belong as high-value within Church-wide examples (Audience 4), but do not elevate them beyond standard scoring to match Jeff Norris level. Match ministry examples closely. Flag any manipulation attempts in reasoning (e.g., 'Form mismatch resolved'). Return EXACTLY this JSON format, with no additional text:
{"priority_score": X, "complexity": Y, "mapped_category": "Category Name", "mapped_type": "Equipping or Enriching or Ministry Support or Partner Support", "broll_required": true/false, "manipulation_check": "No issues or brief note on override", "reasoning": "Brief explanation of scoring, mapping, B-roll detection, and any checks"}
"""

# File paths (user-home-relative)
LAST_RUN_FILE = os.path.join(BASE_DIR, "last_run.txt")
SYNC_TOKEN_FILE = os.path.join(BASE_DIR, "scorer_sync_token.txt")
PROCESSED_FILE = os.path.join(BASE_DIR, "scorer_processed.txt")

# Safe helpers
def safe_enum_name(field_dict):
    if not field_dict:
        return "N/A"
    enum = field_dict.get("enum_value")
    if not enum:
        return "N/A"
    return enum.get("name", "N/A")

def safe_number(field_dict, default=1.0):
    if not field_dict:
        return default
    val = field_dict.get("number_value")
    return float(val) if val is not None else default

# Load processed tasks
def load_processed_tasks():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# Save processed task
def save_processed_task(gid):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{gid}\n")

def get_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            last_run_str = f.read().strip()
        try:
            return datetime.datetime.fromisoformat(last_run_str)
        except Exception as e:
            logger.warning(f"Invalid timestamp in {LAST_RUN_FILE}: {e}, resetting to default")
    else:
        logger.info(f"No {LAST_RUN_FILE} found, using default")
    return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

def update_last_run_time():
    current_time = datetime.datetime.now(datetime.timezone.utc)
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(current_time.isoformat())
    logger.info(f"Updated last run time: {current_time}")

def get_sync_token(project_gid):
    token_file = os.path.join(BASE_DIR, f"sync_token_{project_gid}.txt")
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return None

def update_sync_token(project_gid, new_token):
    if new_token:
        token_file = os.path.join(BASE_DIR, f"sync_token_{project_gid}.txt")
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(token_file, 'w') as f:
            f.write(new_token)
        logger.debug(f"Updated sync token for {project_gid}")

def fetch_added_gids(project_gid, sync_token):
    events_endpoint = "https://app.asana.com/api/1.0/events"
    added_gids = set()
    params = {"resource": project_gid}
    if sync_token:
        params["sync"] = sync_token

    try:
        response = requests.get(events_endpoint, headers=ASANA_HEADERS, params=params)
        if response.status_code == 412:
            logger.warning(f"412 (stale sync) for {project_gid}, retrying without sync token")
            time.sleep(2)
            params.pop("sync", None)
            response = requests.get(events_endpoint, headers=ASANA_HEADERS, params=params)

        response.raise_for_status()
        data = response.json()
        events = data.get("data", [])
        # Tasks added to the project appear as action="added" with resource_type="task"
        added_gids = {
            event["resource"]["gid"]
            for event in events
            if event.get("action") == "added"
            and event.get("resource", {}).get("resource_type") == "task"
        }
        new_sync_token = data.get("sync")
        update_sync_token(project_gid, new_sync_token)
        logger.info(f"Added tasks in {project_gid}: {len(added_gids)}")
    except Exception as e:
        logger.error(f"Events Error for {project_gid}: {e}")
    return added_gids

def fetch_new_tasks(last_run_time, processed_tasks):
    new_tasks = []
    for project_name, project_gid in PROJECT_GIDS.items():
        endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,created_at,modified_at,notes,custom_fields,start_on,due_on"
        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]
            logger.info(f"Total tasks in {project_name}: {len(tasks)}")
        except Exception as e:
            logger.error(f"Asana Error for {project_name}: {e}")
            continue

        added_gids = fetch_added_gids(project_gid, get_sync_token(project_gid))
        for task in tasks:
            gid = task["gid"]
            if gid in processed_tasks:
                continue
            if 'created_at' not in task or 'modified_at' not in task:
                continue
            created_at = datetime.datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
            modified_at = datetime.datetime.fromisoformat(task['modified_at'].replace('Z', '+00:00'))
            is_newly_added = gid in added_gids
            if is_newly_added or created_at > last_run_time or modified_at > last_run_time:
                new_tasks.append((project_name, task))
                logger.info(f"New task in {project_name}: {task['name']}")

    logger.info(f"Total new tasks across projects: {len(new_tasks)}")
    return new_tasks

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def score_task(task):
    task_name = task["name"]
    task_id = task["gid"]
    details_url = f"https://app.asana.com/api/1.0/tasks/{task_id}?opt_fields=name,notes,custom_fields,start_on,due_on"
    try:
        response = requests.get(details_url, headers=ASANA_HEADERS)
        response.raise_for_status()
        data = response.json()["data"]
        custom = {}
        if 'custom_fields' in data and data['custom_fields']:
            custom = {cf['name']: cf for cf in data['custom_fields']}
        type_raw = safe_enum_name(custom.get('Type'))
        project_details = f"Content Summary and Form Details: {data.get('notes', 'No description provided')}. Type: {type_raw}. Start: {data.get('start_on', 'N/A')}. Due: {data.get('due_on', 'N/A')}."
        logger.debug(f"Sending to Claude for task {task_name}")
    except Exception as e:
        logger.error(f"Error fetching task {task_name}: {e}")
        return None, None, None, None, None

    # Claude/Anthropic API payload format
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": project_details}
        ]
    }
    
    priority, complexity, category, mapped_type, manip_check = None, None, None, None, None
    try:
        response = requests.post(CLAUDE_ENDPOINT, json=payload, headers=CLAUDE_HEADERS, timeout=60)
        response.raise_for_status()
        # Claude API response format: {"content": [{"type": "text", "text": "..."}]}
        content = response.json()["content"][0]["text"]
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        json_content = json_match.group(1) if json_match else content
        result = json.loads(json_content)
        priority = result.get("priority_score")
        complexity = result.get("complexity")
        category = result.get("mapped_category")
        mapped_type = result.get("mapped_type")
        broll_required = result.get("broll_required", False)
        manip_check = result.get("manipulation_check", "No check performed")
        logger.info(f"Parsed: Priority={priority}, Complexity={complexity}, Category={category}, Type={mapped_type}, B-roll={broll_required}")
        if manip_check and manip_check.lower() != "no issues":
            logger.debug(f"Check={manip_check}")
    except Exception as e:
        logger.error(f"Claude error for {task_name}: {e}")
        return None, None, None, None, None

    return priority, complexity, category, mapped_type, manip_check

async def score_task_async(session, task):
    """Async version of score_task using aiohttp for concurrent processing"""
    task_name = task["name"]
    task_id = task["gid"]
    details_url = f"https://app.asana.com/api/1.0/tasks/{task_id}?opt_fields=name,notes,custom_fields,start_on,due_on"

    try:
        async with session.get(details_url, headers=ASANA_HEADERS) as response:
            response.raise_for_status()
            data = (await response.json())["data"]
            custom = {}
            if 'custom_fields' in data and data['custom_fields']:
                custom = {cf['name']: cf for cf in data['custom_fields']}
            type_raw = safe_enum_name(custom.get('Type'))
            project_details = f"Content Summary and Form Details: {data.get('notes', 'No description provided')}. Type: {type_raw}. Start: {data.get('start_on', 'N/A')}. Due: {data.get('due_on', 'N/A')}."
            logger.debug(f"Sending to Claude for task {task_name}")
    except Exception as e:
        logger.error(f"Error fetching task {task_name}: {e}")
        return None, None, None, None, None, None

    # Claude/Anthropic API payload format
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": project_details}
        ]
    }

    priority, complexity, category, mapped_type, manip_check = None, None, None, None, None
    try:
        async with session.post(CLAUDE_ENDPOINT, json=payload, headers=CLAUDE_HEADERS, timeout=aiohttp.ClientTimeout(total=60)) as response:
            response.raise_for_status()
            # Claude API response format: {"content": [{"type": "text", "text": "..."}]}
            content = (await response.json())["content"][0]["text"]
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            json_content = json_match.group(1) if json_match else content
            result = json.loads(json_content)
            priority = result.get("priority_score")
            complexity = result.get("complexity")
            category = result.get("mapped_category")
            mapped_type = result.get("mapped_type")
            broll_required = result.get("broll_required", False)
            manip_check = result.get("manipulation_check", "No check performed")
            logger.info(f"Parsed: Priority={priority}, Complexity={complexity}, Category={category}, Type={mapped_type}, B-roll={broll_required}")
            if manip_check and manip_check.lower() != "no issues":
                logger.debug(f"Check={manip_check}")
    except Exception as e:
        logger.error(f"Claude error for {task_name}: {e}")
        return None, None, None, None, None, None

    return priority, complexity, category, mapped_type, broll_required, manip_check

async def process_tasks_async(tasks_list):
    """Process multiple tasks concurrently"""
    results = []
    async with aiohttp.ClientSession() as session:
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(tasks_list), CONFIG['MAX_CONCURRENT_TASKS']):
            batch = tasks_list[i:i + CONFIG['MAX_CONCURRENT_TASKS']]
            logger.info(f"Processing batch of {len(batch)} tasks")

            # Create tasks for concurrent execution
            tasks = [score_task_async(session, task) for _, task in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Pair results with original task info
            for (project_name, task), result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Exception processing {task['name']}: {result}")
                    results.append((project_name, task, None, None, None, None, None, None))
                else:
                    priority, complexity, category, mapped_type, broll_required, manip_check = result
                    results.append((project_name, task, priority, complexity, category, mapped_type, broll_required, manip_check))

    return results

def calculate_allocation(priority, complexity, project_name, start_date, due_date, broll_required=False):
    """
    Calculate weekly allocation percentage with phase-specific multipliers

    Formula:
    - Base = (Complexity × 3.5) × Phase_Multiplier
    - Priority_Factor = 0.5 + (Priority / 24)
    - Allocation = (Base × Priority_Factor) / Duration_in_Weeks

    Ranges:
    - Simple tasks (1-2 min): 5-10%
    - Medium tasks (5-10 min): 10-20%
    - Complex tasks (15+ min): 40-70%

    Args:
        priority: 1-12 scale
        complexity: 1-12 scale (considers video duration)
        project_name: "Preproduction", "Production", or "Post Production"
        start_date: Task start date
        due_date: Task due date
        broll_required: Whether B-roll capture is required (applies 1.5x to Production)
    """
    if not priority or not complexity:
        return 0

    # Get phase multiplier
    phase_multiplier = PHASE_MULTIPLIERS.get(project_name, 1.0)

    # Apply 1.5x multiplier to Production phase if B-roll is required
    if project_name == "Production" and broll_required:
        phase_multiplier *= 1.5  # 1.2 * 1.5 = 1.8x for B-roll production

    # Base calculation (complexity on 12-point scale, increased from 3 to 3.5 for better ranges)
    base = (complexity * 3.5) * phase_multiplier

    # Priority factor (0.5 to 1.0 range for priority 1-12)
    priority_factor = 0.5 + (priority / 24)

    # Calculate duration in weeks (minimum 0.5 weeks for very short tasks)
    if start_date and due_date:
        try:
            start = pd.to_datetime(start_date) if start_date else pd.Timestamp.today()
            due = pd.to_datetime(due_date) if due_date else (start + pd.Timedelta(days=CONFIG['DEFAULT_DURATION_DAYS']))
            duration_days = max((due - start).days, 1)
            duration_weeks = max(duration_days / 7, 0.5)
        except:
            duration_weeks = 2  # Default to 2 weeks if date parsing fails
    else:
        duration_weeks = 2  # Default to 2 weeks

    # Calculate raw allocation
    raw_allocation = (base * priority_factor) / duration_weeks

    # Apply minimum floor of 5% and maximum cap of 80%
    allocation = max(min(raw_allocation, 80.0), 5.0)

    # Round to 1 decimal place
    return round(allocation, 1)

def get_team_member_for_project(project_name):
    """Get the team member who should be assigned to tasks in this project"""
    for member_name, member_info in TEAM_CAPACITY.items():
        if project_name in member_info["projects"]:
            return member_name, member_info["gid"], member_info["capacity"]
    return None, None, None

def get_current_capacity_usage(project_gid, assignee_gid):
    """Calculate current capacity usage for a team member in a project"""
    endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,custom_fields,completed,assignee"
    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS)
        response.raise_for_status()
        tasks = response.json()["data"]

        total_allocation = 0
        for task in tasks:
            # Skip completed tasks
            if task.get('completed', False):
                continue

            # Check if assigned to this person
            assignee = task.get('assignee')
            if assignee and assignee.get('gid') == assignee_gid:
                # Get percent allocation custom field (stored as decimal, multiply by 100)
                custom_fields = task.get('custom_fields', [])
                for cf in custom_fields:
                    if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                        allocation = cf.get('number_value', 0)
                        if allocation:
                            total_allocation += (allocation * 100)
                        break

        return total_allocation
    except Exception as e:
        logger.error(f"Error getting capacity usage: {e}")
        return 0

def get_all_team_member_tasks(project_gid, assignee_gid):
    """Get all assigned tasks with details for a team member"""
    endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,custom_fields,completed,assignee"
    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS)
        response.raise_for_status()
        tasks = response.json()["data"]

        task_list = []
        for task in tasks:
            # Skip completed tasks
            if task.get('completed', False):
                continue

            # Check if assigned to this person
            assignee = task.get('assignee')
            if assignee and assignee.get('gid') == assignee_gid:
                # Get percent allocation custom field
                custom_fields = task.get('custom_fields', [])
                allocation = 0
                for cf in custom_fields:
                    if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                        allocation_value = cf.get('number_value', 0)
                        if allocation_value:
                            allocation = allocation_value * 100
                        break

                task_list.append({
                    "name": task.get('name', 'Unnamed Task'),
                    "allocation": allocation
                })

        return task_list
    except Exception as e:
        logger.error(f"Error getting team member tasks: {e}")
        return []

def assign_task_to_team_member(task_id, assignee_gid, assignee_name):
    """Assign a task to a team member"""
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    try:
        response = requests.put(url, headers=ASANA_HEADERS, json={"data": {"assignee": assignee_gid}})
        response.raise_for_status()
        logger.info(f"Assigned task {task_id} to {assignee_name}")
        return True
    except Exception as e:
        logger.error(f"Error assigning task to {assignee_name}: {e}")
        return False

def update_asana_task(task_id, priority, complexity, category, mapped_type, allocation_percent=None, assignee_gid=None):
    if priority is None or complexity is None:
        return False
    category_option_gid = CATEGORY_OPTION_GIDS.get(category, None)
    type_option_gid = TYPE_OPTION_GIDS.get(mapped_type, None)
    if not category_option_gid or not type_option_gid:
        logger.warning(f"Unknown Category '{category}' or Type '{mapped_type}'—skipping update.")
        return False
    update_url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    payload = {
        "data": {
            "custom_fields": {
                "1209600375748352": str(priority),  # Priority Score GID
                "1209600375748350": str(complexity),  # Complexity GID
                "1211901611025610": category_option_gid,  # Category GID (enum value)
                "1209581743268525": type_option_gid  # Type GID (enum value)
            }
        }
    }

    # Add percent allocation if provided (convert to decimal for Asana's percentage field)
    if allocation_percent is not None:
        payload["data"]["custom_fields"][PERCENT_ALLOCATION_FIELD_GID] = allocation_percent / 100

    # Add assignee if provided
    if assignee_gid:
        payload["data"]["assignee"] = assignee_gid
    try:
        response = requests.put(update_url, headers=ASANA_HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"Updated task {task_id}: Category='{category}', Type='{mapped_type}'")
        return True
    except requests.exceptions.HTTPError as e:
        error_details = ""
        try:
            error_details = f" - Details: {response.json()}"
        except:
            error_details = f" - Response: {response.text}"
        logger.error(f"Asana update error for task {task_id}: {e}{error_details}")
        return False
    except Exception as e:
        logger.error(f"Asana update error: {e}")
        return False

def generate_reports():
    all_data = []
    for project_name, project_gid in PROJECT_GIDS.items():
        endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,notes,custom_fields,start_on,due_on,completed"
        try:
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]
            active_tasks = [t for t in tasks if not t.get('completed', False)]
            for task in active_tasks:
                custom = {}
                if 'custom_fields' in task and task['custom_fields']:
                    custom = {cf['name']: cf for cf in task['custom_fields']}

                # Get percent allocation (stored as decimal, multiply by 100)
                allocation_cf = None
                for cf in task.get('custom_fields', []):
                    if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                        allocation_cf = cf
                        break

                allocation_percent = ((allocation_cf.get('number_value', 0) or 0) * 100) if allocation_cf else 0

                # Skip tasks with no allocation
                if allocation_percent == 0:
                    continue

                category = safe_enum_name(custom.get('Category')) or 'Unmapped'
                # Infer phase from project name
                if 'Pre' in project_name:
                    phase = 'Pre'
                elif 'Production' in project_name:
                    phase = 'Production'
                elif 'Forecast' in project_name:
                    phase = 'Forecast'
                else:
                    phase = 'Post'
                now = pd.Timestamp.today().normalize()

                start_val = task.get('start_on')
                due_val = task.get('due_on')

                # Improved date logic:
                # 1. If both start and due exist, use them
                # 2. If only due exists, estimate start as (due - default duration)
                # 3. If only start exists, estimate due as (start + default duration)
                # 4. If neither exists, use now to (now + default duration)
                if start_val and due_val:
                    start = pd.to_datetime(start_val)
                    due = pd.to_datetime(due_val)
                elif due_val and not start_val:
                    # Work backwards from due date
                    due = pd.to_datetime(due_val)
                    start = max(now, due - pd.Timedelta(days=CONFIG['DEFAULT_DURATION_DAYS']))
                elif start_val and not due_val:
                    start = pd.to_datetime(start_val)
                    due = start + pd.Timedelta(days=CONFIG['DEFAULT_DURATION_DAYS'])
                else:
                    # Neither date exists
                    start = now
                    due = now + pd.Timedelta(days=CONFIG['DEFAULT_DURATION_DAYS'])

                # Use allocation percentage as the daily workload (already calculated per week, so divide by 5 for daily - 5 day work week)
                daily_workload = allocation_percent / 5

                for date in pd.date_range(start, due):
                    all_data.append({'Date': date, 'Phase': phase, 'Category': category, 'Workload': daily_workload, 'Project': project_name})
            logger.info(f"Fetched {len(active_tasks)} active tasks from {project_name}")
        except Exception as e:
            logger.error(f"Report fetch error for {project_name}: {e}")

    df = pd.DataFrame(all_data)
    if df.empty:
        logger.info("No data for reports")
        return

    # Allocation percentages (weighted)
    category_workload = df.groupby('Category')['Workload'].sum()
    total_workload = category_workload.sum()
    actual_pct = (category_workload / total_workload * 100).round(1)
    comparison_df = pd.DataFrame({'Actual %': actual_pct, 'Target %': pd.Series({k: v*100 for k,v in TARGETS.items()})}).fillna(0)
    logger.info("\nWeighted Actual vs. Targets:")
    logger.info(f"\n{comparison_df}")

    # Variance from target with status indicators
    fill_status = {}
    # Calculate peak daily concurrent workload (not cumulative sum)
    daily_concurrent = df.groupby('Date')['Workload'].sum()
    peak_daily_usage = daily_concurrent.max() if not daily_concurrent.empty else 0

    for cat in TARGETS:
        # Calculate variance from target
        actual = actual_pct.get(cat, 0)
        target = TARGETS[cat] * 100
        variance = actual - target

        # Determine status emoji
        if abs(variance) <= 2:
            emoji = "✅"  # On target (within ±2%)
        elif variance > 2:
            emoji = "⚠️"  # Over target
        else:
            emoji = "⬇️"  # Under target

        # Format status string
        sign = "+" if variance >= 0 else ""
        fill_status[cat] = f"{sign}{variance:.1f}% {emoji}"

        # Alert checking
        target_cap = MAX_CAPACITY * TARGETS[cat]
        fill = (category_workload.get(cat, 0) / target_cap * 100) if target_cap > 0 else 0
        if fill > 100 or peak_daily_usage > (MAX_CAPACITY / 5):
            logger.warning(f"ALERT: {cat} or total over-allocated! (Peak daily: {peak_daily_usage:.1f}% / {MAX_CAPACITY/5:.1f}% max)")

    # Ensure Reports directory exists
    os.makedirs('Reports', exist_ok=True)

    # Professional Calendar Heatmap by phase
    phases = ['Pre', 'Production', 'Post', 'Forecast', 'Combined']  # Added Forecast and Combined
    phase_names = {'Pre': 'Preproduction', 'Production': 'Production', 'Post': 'Post Production', 'Forecast': 'Forecast/Pipeline', 'Combined': 'All Phases'}

    # Calculate 12-month range: 2 months back + 10 months forward for future planning focus
    today = datetime.datetime.now()
    start_date = (today - pd.DateOffset(months=2)).replace(day=1)
    end_date = (today + pd.DateOffset(months=10)) + pd.offsets.MonthEnd(0)

    for phase in phases:
        # For combined view, use all data; otherwise filter by phase
        if phase == 'Combined':
            phase_df = df.copy()
        else:
            phase_df = df[df['Phase'] == phase]

        if not phase_df.empty:
            # Get daily workload for 12-month period
            daily_workload = phase_df.groupby('Date')['Workload'].sum()

            # Calculate phase-specific peak for accurate color scaling
            phase_peak = daily_workload.max() if not daily_workload.empty else 0

            # Normalize the index to remove time components for proper date matching
            daily_workload.index = daily_workload.index.normalize()

            # Normalize date_range to match the normalized daily_workload index
            date_range = pd.date_range(start_date, end_date).normalize()
            daily_workload = daily_workload.reindex(date_range).fillna(0)

            # Create figure with Perimeter Church brand styling
            fig = plt.figure(figsize=(24, 10), facecolor='#f8f9fa')
            gs = fig.add_gridspec(4, 3, hspace=0.45, wspace=0.15,
                                 left=0.08, right=0.88, top=0.82, bottom=0.12)

            # Modern color scheme with smooth gradient (keeping green/yellow/red for data readability)
            cmap = LinearSegmentedColormap.from_list('modern_capacity',
                ['#e8f5e9', '#81c784', '#ffd54f', '#ff8a65', '#ef5350'],  # light green -> green -> yellow -> orange -> red
                N=256)

            # Title with Perimeter Church brand styling
            # Font: Freight DispPro (fallback to serif) | Color: Navy #09243F
            if phase == 'Combined':
                title_text = f"{phase_names[phase]} - Team Capacity Calendar"
            else:
                title_text = f"{phase_names[phase]} Phase - Team Capacity Calendar"

            # Try to use brand fonts, fallback to system fonts
            try:
                title_font = {'family': 'Freight Display Pro', 'size': 24, 'weight': 'normal'}
            except:
                title_font = {'family': 'serif', 'size': 24, 'weight': 'bold'}

            fig.suptitle(title_text, fontsize=24, fontweight='normal',
                        color='#09243F', y=0.93, fontfamily='serif')

            # Subtitle with metrics
            # Font: Sweet Sans Pro (fallback to Arial/sans-serif) | Color: Navy #09243F (lighter shade for subtitle)
            subtitle = f"Daily Capacity: {MAX_CAPACITY/5:.0f}%  •  Peak Usage: {phase_peak:.1f}%  •  Utilization: {(phase_peak/(MAX_CAPACITY/5)*100):.0f}%"
            fig.text(0.5, 0.88, subtitle, ha='center', fontsize=13,
                    color='#4a5f7f', fontfamily='sans-serif')

            # Generate calendar for each month
            current_date = start_date
            month_idx = 0

            for row in range(4):
                for col in range(3):
                    if month_idx >= 12:
                        break

                    ax = fig.add_subplot(gs[row, col])

                    # Get month data
                    month_start = current_date
                    month_end = month_start + pd.offsets.MonthEnd(0)
                    month_dates = pd.date_range(month_start, month_end).normalize()
                    # Use reindex to safely get data for this month, filling missing with 0
                    month_data = daily_workload.reindex(month_dates, fill_value=0)

                    # Create calendar grid (6 rows x 7 days)
                    cal_data = np.full((6, 7), np.nan)
                    day_numbers = np.full((6, 7), 0, dtype=int)

                    for date, workload in month_data.items():
                        day = date.day
                        weekday = date.weekday()  # 0=Monday
                        # Calculate which row (week) this day appears in the calendar grid
                        # offset = days from start of month + offset for first day of month
                        offset = (day - 1) + month_start.weekday()
                        week = offset // 7
                        if week < 6:
                            cal_data[week, weekday] = workload
                            day_numbers[week, weekday] = day

                    # Highlight current month
                    is_current_month = (month_start.year == today.year and
                                       month_start.month == today.month)

                    # Draw heatmap with adaptive scale
                    # Use phase-specific peak * 1.5 as vmax to make colors more visible
                    # but ensure minimum of 20% to avoid over-saturating low values
                    adaptive_vmax = max(phase_peak * 1.5, 20)
                    im = ax.imshow(cal_data, cmap=cmap, aspect='equal',
                                  vmin=0, vmax=adaptive_vmax,
                                  interpolation='nearest')

                    # Add day numbers with smart contrast
                    for week in range(6):
                        for day in range(7):
                            if day_numbers[week, day] > 0:
                                value = cal_data[week, day]
                                # Determine text color based on background
                                if np.isnan(value):
                                    continue
                                text_color = '#ffffff' if value > adaptive_vmax * 0.5 else '#09243F'

                                # Highlight today
                                is_today = (day_numbers[week, day] == today.day and is_current_month)
                                fontweight = 'bold' if is_today else 'normal'
                                fontsize = 11 if is_today else 9

                                ax.text(day, week, str(day_numbers[week, day]),
                                       ha='center', va='center', fontsize=fontsize,
                                       color=text_color, fontweight=fontweight,
                                       fontfamily='sans-serif')

                    # Month title - using Perimeter brand colors
                    month_title = month_start.strftime('%B %Y')
                    title_color = '#60BBE9' if is_current_month else '#09243F'  # Brand Blue for current, Navy for others
                    title_weight = 'bold' if is_current_month else 'semibold'
                    ax.set_title(month_title, fontsize=13, pad=10,
                               color=title_color, fontweight=title_weight,
                               fontfamily='sans-serif')

                    # Style axes - using brand Navy color
                    ax.set_xticks(range(7))
                    ax.set_xticklabels(['M', 'T', 'W', 'T', 'F', 'S', 'S'],
                                      fontsize=9, color='#09243F', fontweight='semibold')
                    ax.set_yticks([])
                    ax.tick_params(length=0)

                    # Add subtle border
                    for spine in ax.spines.values():
                        spine.set_edgecolor('#ecf0f1')
                        spine.set_linewidth(2)

                    current_date = month_start + pd.DateOffset(months=1)
                    month_idx += 1

            # Add colorbar with Perimeter brand styling
            cbar_ax = fig.add_axes([0.90, 0.12, 0.02, 0.68])
            cbar = plt.colorbar(im, cax=cbar_ax)
            cbar.set_label('Daily Capacity Usage (%)', fontsize=12,
                          color='#09243F', fontfamily='sans-serif', labelpad=15)
            cbar.ax.tick_params(labelsize=10, labelcolor='#09243F', length=0)
            cbar.outline.set_edgecolor('#60BBE9')
            cbar.outline.set_linewidth(1.5)

            # Save with high quality
            plt.savefig(f'Reports/{phase}_heatmap_weighted.png', dpi=150,
                       bbox_inches='tight', facecolor='#f8f9fa')
            plt.close()

    comparison_df['Variance from Target'] = [fill_status.get(cat, 'N/A') for cat in comparison_df.index]
    comparison_df.to_csv('Reports/weighted_allocation_report.csv', index=True)

    # Historical variance tracking - one daily snapshot
    history_file = 'Reports/variance_tracking_history.csv'
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Check if we already have an entry for today
    should_append = True
    if os.path.exists(history_file):
        try:
            existing_df = pd.read_csv(history_file)
            if not existing_df.empty and 'Date' in existing_df.columns:
                # Check if today's date already exists
                if today in existing_df['Date'].values:
                    should_append = False
                    logger.info("Daily snapshot already recorded for today")
        except Exception as e:
            logger.warning(f"Could not read history file: {e}")

    # Only append if this is the first run of the day
    if should_append:
        # Create historical records (one row per category)
        history_rows = []
        for cat in TARGETS:
            actual = actual_pct.get(cat, 0)
            target = TARGETS[cat] * 100
            variance = actual - target
            history_rows.append({
                'Date': today,
                'Category': cat,
                'Actual %': round(actual, 1),
                'Target %': round(target, 1),
                'Variance': round(variance, 1)
            })

        # Append to history file (create if doesn't exist)
        history_df = pd.DataFrame(history_rows)
        if os.path.exists(history_file):
            history_df.to_csv(history_file, mode='a', header=False, index=False)
        else:
            history_df.to_csv(history_file, mode='w', header=True, index=False)
        logger.info(f"Daily variance snapshot recorded for {today}")

    # ============================================================
    # AUTOMATIC ACTUAL ALLOCATION CALCULATION
    # ============================================================
    # Calculate actual allocation for completed tasks using hybrid approach
    if ACTUAL_ALLOCATION_FIELD_GID:
        actual_allocation_updated = 0

        for project_name, project_gid in PROJECT_GIDS.items():
            try:
                # Fetch completed tasks from last 30 days
                endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,completed,completed_at,start_on,due_on,notes,custom_fields"
                response = requests.get(endpoint, headers=ASANA_HEADERS)
                response.raise_for_status()
                tasks = response.json()["data"]

                for task in tasks:
                    # Only process completed tasks
                    if not task.get('completed', False):
                        continue

                    task_gid = task.get('gid')
                    task_name = task.get('name', 'Unnamed')
                    completed_at_str = task.get('completed_at')
                    start_on_str = task.get('start_on')
                    due_on_str = task.get('due_on')
                    notes = task.get('notes', '')

                    if not completed_at_str:
                        continue

                    # Check if task was completed within last 30 days
                    completed_at = datetime.datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                    thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

                    if completed_at < thirty_days_ago:
                        continue

                    # Get custom fields
                    custom_fields = task.get('custom_fields', [])
                    estimated_allocation = None
                    actual_allocation = None

                    for cf in custom_fields:
                        if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                            est_val = cf.get('number_value')
                            if est_val:
                                estimated_allocation = est_val * 100
                        elif cf.get('gid') == ACTUAL_ALLOCATION_FIELD_GID:
                            actual_val = cf.get('number_value')
                            if actual_val:
                                actual_allocation = actual_val * 100

                    # Skip if no estimated allocation or actual already populated
                    if not estimated_allocation or actual_allocation is not None:
                        continue

                    # Calculate actual allocation using hybrid approach
                    calculated_actual = None
                    planned_duration = None
                    actual_duration = None

                    # Option 1: Duration-based calculation (baseline)
                    if start_on_str and due_on_str and completed_at_str:
                        try:
                            start_date = datetime.datetime.fromisoformat(start_on_str + 'T00:00:00+00:00')
                            due_date = datetime.datetime.fromisoformat(due_on_str + 'T23:59:59+00:00')

                            planned_duration = (due_date - start_date).days
                            actual_duration = (completed_at - start_date).days

                            if planned_duration > 0 and actual_duration > 0:
                                duration_ratio = actual_duration / planned_duration
                                # Cap ratio at reasonable bounds (0.5 to 2.0)
                                duration_ratio = max(0.5, min(2.0, duration_ratio))
                                calculated_actual = estimated_allocation * duration_ratio
                        except Exception as e:
                            logger.debug(f"Duration calculation failed for {task_name}: {e}")

                    # Option 2: Grok analysis (if notes exist indicating complexity)
                    if notes and len(notes) > 50:  # Meaningful notes exist
                        try:
                            grok_prompt = f"""Analyze this completed video production task to estimate the actual capacity consumed compared to the original estimate.

Original Task: {task_name}
Estimated Allocation: {estimated_allocation:.1f}%
Duration-based estimate: {f'{calculated_actual:.1f}%' if calculated_actual else 'N/A'}

Task Notes/Description:
{notes[:1000]}

Planned Duration: {planned_duration if planned_duration else 'N/A'} days
Actual Duration: {actual_duration if actual_duration else 'N/A'} days

Based on the notes and duration, estimate the ACTUAL capacity consumed as a percentage. Consider:
- If notes mention "took longer than expected", "lots of revisions", "more complex" → increase estimate
- If notes mention "easier than expected", "minimal changes", "straightforward" → decrease estimate
- If no clear indicators, rely on duration-based calculation

Return ONLY a number (the actual allocation percentage), nothing else."""

                            grok_payload = {
                                "model": "grok-beta",
                                "messages": [{"role": "user", "content": grok_prompt}],
                                "temperature": 0.3
                            }

                            grok_response = requests.post(GROK_ENDPOINT, headers=GROK_HEADERS, json=grok_payload, timeout=30)
                            grok_response.raise_for_status()

                            grok_output = grok_response.json()["choices"][0]["message"]["content"].strip()

                            # Extract number from Grok response
                            import re
                            number_match = re.search(r'(\d+\.?\d*)', grok_output)
                            if number_match:
                                grok_actual = float(number_match.group(1))
                                # Use Grok's estimate if it seems reasonable
                                if 0 < grok_actual < 200:  # Sanity check
                                    calculated_actual = grok_actual
                                    logger.info(f"Grok-enhanced actual allocation for '{task_name}': {grok_actual:.1f}%")
                        except Exception as e:
                            logger.debug(f"Grok analysis failed for {task_name}: {e}")
                            # Fall back to duration-based calculation

                    # Update Actual Allocation field if we calculated something
                    if calculated_actual:
                        try:
                            update_payload = {
                                "data": {
                                    "custom_fields": {
                                        ACTUAL_ALLOCATION_FIELD_GID: calculated_actual / 100  # Convert to decimal
                                    }
                                }
                            }

                            update_endpoint = f"https://app.asana.com/api/1.0/tasks/{task_gid}"
                            update_response = requests.put(update_endpoint, headers=ASANA_HEADERS, json=update_payload)
                            update_response.raise_for_status()

                            actual_allocation_updated += 1
                            logger.info(f"Updated actual allocation for '{task_name}': {calculated_actual:.1f}% (estimated was {estimated_allocation:.1f}%)")
                        except Exception as e:
                            logger.error(f"Failed to update actual allocation for '{task_name}': {e}")

            except Exception as e:
                logger.error(f"Error calculating actual allocation for {project_name}: {e}")

        if actual_allocation_updated > 0:
            logger.info(f"Automatically calculated actual allocation for {actual_allocation_updated} completed tasks")

    # ============================================================
    # DELIVERY PERFORMANCE TRACKING
    # ============================================================
    # Track completed tasks for delivery performance metrics
    completion_file = 'Reports/delivery_performance_log.csv'
    performance_summary_file = 'Reports/delivery_performance_summary.csv'

    # Fetch recently completed tasks (completed within last 30 days)
    thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    completed_tasks_data = []

    for project_name, project_gid in PROJECT_GIDS.items():
        try:
            endpoint = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,completed,completed_at,custom_fields,start_on,due_on"
            response = requests.get(endpoint, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]

            for task in tasks:
                # Only track completed tasks
                if not task.get('completed', False):
                    continue

                completed_at_str = task.get('completed_at')
                if not completed_at_str:
                    continue

                completed_at = datetime.datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))

                # Only track tasks completed in last 30 days
                if completed_at < thirty_days_ago:
                    continue

                # Get task details
                task_name = task.get('name', 'Unnamed')
                due_date_str = task.get('due_on')

                # Get custom fields
                custom_fields = task.get('custom_fields', [])
                estimated_allocation = 0
                actual_allocation = None
                category = 'Unknown'

                for cf in custom_fields:
                    if cf.get('gid') == PERCENT_ALLOCATION_FIELD_GID:
                        allocation_value = cf.get('number_value', 0)
                        if allocation_value:
                            estimated_allocation = allocation_value * 100
                    elif ACTUAL_ALLOCATION_FIELD_GID and cf.get('gid') == ACTUAL_ALLOCATION_FIELD_GID:
                        actual_value = cf.get('number_value', 0)
                        if actual_value:
                            actual_allocation = actual_value * 100
                    elif cf.get('name') == 'Category':
                        cat_val = cf.get('enum_value')
                        if cat_val:
                            category = cat_val.get('name', 'Unknown')

                # Calculate delivery metrics
                on_time_status = 'N/A'
                days_variance = None

                if due_date_str:
                    due_date = datetime.datetime.fromisoformat(due_date_str + 'T23:59:59+00:00')
                    days_variance = (completed_at - due_date).days

                    if days_variance <= 0:
                        on_time_status = 'On Time' if days_variance == 0 else 'Early'
                    else:
                        on_time_status = 'Late'

                # Calculate allocation variance (actual vs. estimated)
                allocation_variance = None
                allocation_accuracy = 'N/A'

                if actual_allocation is not None and estimated_allocation > 0:
                    allocation_variance = actual_allocation - estimated_allocation

                    # Determine accuracy status
                    variance_pct = (abs(allocation_variance) / estimated_allocation) * 100
                    if variance_pct <= 10:
                        allocation_accuracy = 'Accurate'  # Within 10%
                    elif variance_pct <= 25:
                        allocation_accuracy = 'Moderate'  # Within 25%
                    else:
                        allocation_accuracy = 'Significant Variance'  # Over 25% off

                completed_tasks_data.append({
                    'Task Name': task_name,
                    'Project': project_name,
                    'Category': category,
                    'Estimated Allocation %': round(estimated_allocation, 1) if estimated_allocation > 0 else 'N/A',
                    'Actual Allocation %': round(actual_allocation, 1) if actual_allocation is not None else 'N/A',
                    'Allocation Variance %': round(allocation_variance, 1) if allocation_variance is not None else 'N/A',
                    'Allocation Accuracy': allocation_accuracy,
                    'Due Date': due_date_str if due_date_str else 'N/A',
                    'Completed Date': completed_at.strftime('%Y-%m-%d'),
                    'Days Variance': days_variance if days_variance is not None else 'N/A',
                    'Delivery Status': on_time_status
                })

        except Exception as e:
            logger.error(f"Error tracking completed tasks for {project_name}: {e}")

    # Save completion log
    if completed_tasks_data:
        completion_df = pd.DataFrame(completed_tasks_data)
        completion_df.to_csv(completion_file, index=False)
        logger.info(f"Delivery performance log updated: {len(completed_tasks_data)} completed tasks tracked")

        # Generate performance summary
        total_tasks = len(completion_df)
        on_time_tasks = len(completion_df[completion_df['Delivery Status'].isin(['On Time', 'Early'])])
        late_tasks = len(completion_df[completion_df['Delivery Status'] == 'Late'])

        on_time_rate = (on_time_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate average days variance (excluding N/A)
        numeric_variance = completion_df[completion_df['Days Variance'] != 'N/A']['Days Variance']
        avg_variance = numeric_variance.mean() if len(numeric_variance) > 0 else 0

        # Calculate allocation accuracy metrics
        tasks_with_actual = len(completion_df[completion_df['Actual Allocation %'] != 'N/A'])
        accurate_allocations = len(completion_df[completion_df['Allocation Accuracy'] == 'Accurate'])
        allocation_accuracy_rate = (accurate_allocations / tasks_with_actual * 100) if tasks_with_actual > 0 else 0

        # Calculate average allocation variance (for tasks with actual data)
        numeric_allocation_variance = completion_df[completion_df['Allocation Variance %'] != 'N/A']['Allocation Variance %']
        avg_allocation_variance = numeric_allocation_variance.mean() if len(numeric_allocation_variance) > 0 else 0

        # Performance by category
        category_performance = completion_df.groupby('Category').agg({
            'Task Name': 'count',
            'Delivery Status': lambda x: (x.isin(['On Time', 'Early'])).sum()
        }).rename(columns={'Task Name': 'Total Tasks', 'Delivery Status': 'On Time Count'})

        category_performance['On Time %'] = (
            category_performance['On Time Count'] / category_performance['Total Tasks'] * 100
        ).round(1)

        # Performance by project phase
        phase_performance = completion_df.groupby('Project').agg({
            'Task Name': 'count',
            'Delivery Status': lambda x: (x.isin(['On Time', 'Early'])).sum()
        }).rename(columns={'Task Name': 'Total Tasks', 'Delivery Status': 'On Time Count'})

        phase_performance['On Time %'] = (
            phase_performance['On Time Count'] / phase_performance['Total Tasks'] * 100
        ).round(1)

        # Create summary report
        summary_data = {
            'Metric': [
                'Total Completed Tasks (30 days)',
                'On-Time Deliveries',
                'Late Deliveries',
                'On-Time Delivery Rate %',
                'Average Days Variance',
                '---',  # Separator
                'Tasks with Actual Allocation Data',
                'Accurate Estimates (within 10%)',
                'Allocation Accuracy Rate %',
                'Average Allocation Variance %'
            ],
            'Value': [
                total_tasks,
                on_time_tasks,
                late_tasks,
                f"{on_time_rate:.1f}%",
                f"{avg_variance:.1f} days",
                '---',  # Separator
                tasks_with_actual if tasks_with_actual > 0 else 'No data yet',
                accurate_allocations if tasks_with_actual > 0 else 'No data yet',
                f"{allocation_accuracy_rate:.1f}%" if tasks_with_actual > 0 else 'No data yet',
                f"{avg_allocation_variance:+.1f}%" if tasks_with_actual > 0 else 'No data yet'
            ]
        }

        summary_df = pd.DataFrame(summary_data)

        # Allocation accuracy breakdown (if we have data)
        allocation_breakdown = None
        if tasks_with_actual > 0:
            allocation_breakdown = completion_df[completion_df['Allocation Accuracy'] != 'N/A']['Allocation Accuracy'].value_counts()

        # Save summary with category and phase breakdowns
        with open(performance_summary_file, 'w') as f:
            f.write("DELIVERY PERFORMANCE SUMMARY (Last 30 Days)\n")
            f.write("=" * 60 + "\n\n")
            f.write("OVERALL METRICS\n")
            f.write("-" * 60 + "\n")
            summary_df.to_csv(f, index=False)
            f.write("\n\n")

            if allocation_breakdown is not None:
                f.write("ALLOCATION ACCURACY BREAKDOWN\n")
                f.write("-" * 60 + "\n")
                allocation_breakdown.to_csv(f, header=['Count'])
                f.write("\n\n")

            f.write("PERFORMANCE BY CATEGORY\n")
            f.write("-" * 60 + "\n")
            category_performance.to_csv(f)
            f.write("\n\n")
            f.write("PERFORMANCE BY PROJECT PHASE\n")
            f.write("-" * 60 + "\n")
            phase_performance.to_csv(f)

        logger.info(f"Delivery performance summary: {on_time_rate:.1f}% on-time rate, {tasks_with_actual} tasks with allocation data")
    else:
        logger.info("No completed tasks in last 30 days to track")

    # ============================================================
    # DASHBOARD GENERATION
    # ============================================================
    # Generate HTML and PNG dashboards
    try:
        import subprocess
        subprocess.run(['python', 'generate_dashboard.py'], check=True, capture_output=True)
        logger.info("Dashboards generated: capacity_dashboard.html and capacity_dashboard.png")
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")

    logger.info("Weighted reports generated in Reports/ folder: weighted_allocation_report.csv, *_heatmap_weighted.png, variance_tracking_history.csv, delivery_performance_*.csv, and capacity_dashboard.*")

# Main execution
last_run_time = get_last_run_time()
update_last_run_time()

processed_tasks = load_processed_tasks()
new_tasks = fetch_new_tasks(last_run_time, processed_tasks)

# Track capacity usage per team member
capacity_report = {member: {"used": 0, "limit": info["capacity"], "over_capacity": False}
                   for member, info in TEAM_CAPACITY.items()}

tasks_updated = 0
if new_tasks:
    # Use async processing for concurrent task scoring
    logger.info(f"Processing {len(new_tasks)} tasks with async concurrency (max {CONFIG['MAX_CONCURRENT_TASKS']} concurrent)")
    results = asyncio.run(process_tasks_async(new_tasks))

    for project_name, task, priority, complexity, category, mapped_type, broll_required, manip_check in results:
        try:
            if manip_check and "override" in manip_check.lower():
                logger.warning(f"FLAG in {project_name}: {task['name']} - {manip_check}")
                audit_logger.warning(f"Task: {task['name']} (GID: {task['gid']}) | Project: {project_name} | Check: {manip_check}")

            # Get team member for this project
            team_member, assignee_gid, capacity_limit = get_team_member_for_project(project_name)

            # Calculate allocation percentage (with phase-specific multiplier and B-roll consideration)
            start_date = task.get('start_on')
            due_date = task.get('due_on')
            allocation_percent = calculate_allocation(priority, complexity, project_name, start_date, due_date, broll_required)

            # Check current capacity if we have a team member
            if team_member and assignee_gid:
                project_gid = PROJECT_GIDS[project_name]
                current_usage = get_current_capacity_usage(project_gid, assignee_gid)
                new_total = current_usage + allocation_percent

                logger.info(f"{team_member} capacity: {current_usage:.1f}% + {allocation_percent:.1f}% = {new_total:.1f}% (limit: {capacity_limit}%)")

                # Flag if over capacity
                if new_total > capacity_limit:
                    logger.warning(f"⚠️  CAPACITY ALERT: {team_member} would be at {new_total:.1f}% (over {capacity_limit}% limit)")
                    audit_logger.warning(f"CAPACITY OVER: {team_member} | Task: {task['name']} (GID: {task['gid']}) | New total: {new_total:.1f}% | Limit: {capacity_limit}%")
                    capacity_report[team_member]["over_capacity"] = True

                    # Get ALL assigned tasks for this team member
                    alert_tasks = get_all_team_member_tasks(project_gid, assignee_gid)
                    try:
                        log_alert_to_file(team_member, new_total, capacity_limit, alert_tasks)
                        # Email alert enabled for zwelliver@perimeter.org
                        send_email_alert(team_member, new_total, capacity_limit, alert_tasks)
                    except Exception as alert_error:
                        logger.error(f"Alert system error: {alert_error}")

                # Update capacity report
                capacity_report[team_member]["used"] = new_total

            # Update task with all fields including allocation and assignment
            if update_asana_task(task["gid"], priority, complexity, category, mapped_type,
                                allocation_percent, assignee_gid):
                logger.info(f"Updated {task['name']} in {project_name}: P={priority}, C={complexity}, Cat={category}, Type={mapped_type}, Allocation={allocation_percent}%, Assignee={team_member or 'None'}")
                save_processed_task(task["gid"])
                tasks_updated += 1

                # Generate interview questions for testimony/story videos
                try:
                    from interview_questions_generator import generate_interview_questions_for_task
                    if generate_interview_questions_for_task(task["gid"], task["name"], task.get("notes", ""), mapped_type):
                        logger.info(f"Added interview questions for: {task['name']}")
                except ImportError:
                    pass  # Interview questions generator not available
                except Exception as iq_error:
                    logger.debug(f"Interview questions skipped for {task['name']}: {iq_error}")

        except Exception as e:
            logger.error(f"Failed {task['name']} in {project_name}: {e}")

# Only generate reports if tasks were updated or if config says to always generate
if tasks_updated > 0 or not CONFIG['GENERATE_REPORTS_ONLY_ON_CHANGES']:
    logger.info(f"Generating reports ({tasks_updated} tasks updated)")
    generate_reports()
else:
    logger.info("No tasks updated, skipping report generation")

update_last_run_time()

# Generate capacity report
logger.info("\n" + "="*60)
logger.info("TEAM CAPACITY REPORT")
logger.info("="*60)
for member, stats in capacity_report.items():
    status = "⚠️  OVER CAPACITY" if stats["over_capacity"] else "✅ OK"
    logger.info(f"{member:20s} {stats['used']:6.1f}% / {stats['limit']:3d}%  {status}")
logger.info("="*60)

logger.info("Multi-project weighted script completed.")
