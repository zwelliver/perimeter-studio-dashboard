"""
Perimeter Church Communications Department - Centralized Configuration (ClickUp)
==================================================================================

ClickUp version of the centralized config. Maps the same automation system
to ClickUp's hierarchy and API. Drop-in replacement for config.py if
the department migrates from Asana to ClickUp.

ClickUp Hierarchy (vs Asana):
  Asana Workspace  →  ClickUp Workspace (called "team" in API)
  Asana Team       →  ClickUp Space
  Asana Project    →  ClickUp List (inside optional Folders)
  Asana Section    →  ClickUp Status (on each List)
  Asana Custom Field →  ClickUp Custom Field (set via separate endpoint)
  Asana Task       →  ClickUp Task

Key API differences:
  - Base URL: https://api.clickup.com/api/v2  (not app.asana.com/api/1.0)
  - Auth: "Authorization: <token>"  (no "Bearer" prefix)
  - Tasks live in Lists (POST /list/{list_id}/task)
  - Custom fields are SET via a dedicated endpoint, not via task update
  - Rate limits: 100 req/min (Free/Unlimited), 1000 (Business+), 10000 (Enterprise)
  - Webhooks: per-location (Space, Folder, List, or Task level)

Usage in any script:
    from config_clickup import CONFIG, TEAM, LISTS, FIELDS, SCORING, ALERTS, PATHS

Maintained by: Zach Welliver
Last updated: 2026-02-06
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


# =============================================================================
# WORKSPACE  (ClickUp calls this "team" in the API)
# =============================================================================

WORKSPACE_ID = "<CLICKUP_TEAM_ID>"  # Get via GET /api/v2/team


# =============================================================================
# API CREDENTIALS (all from .env - never hardcode secrets)
# =============================================================================

API = {
    # ClickUp
    "CLICKUP_TOKEN": os.getenv("CLICKUP_API_TOKEN"),
    "CLICKUP_BASE_URL": "https://api.clickup.com/api/v2",

    # Grok (xAI) — unchanged, AI scoring is PM-tool-agnostic
    "GROK_API_KEY": os.getenv("GROK_API_KEY"),
    "GROK_ENDPOINT": "https://api.x.ai/v1/chat/completions",
    "GROK_MODEL": "grok-4-fast-non-reasoning",
    "GROK_MODEL_ANALYSIS": "grok-beta",

    # Image Generation — unchanged
    "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN"),
    "REPLICATE_MODEL": "black-forest-labs/flux-2-max",
    "SD_API_KEY": os.getenv("STABLE_DIFFUSION_API_KEY"),
    "SD_ENDPOINT": "https://api.stability.ai/v2beta/stable-image/generate/ultra",

    # Email / SMTP — unchanged
    "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")),
    "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
    "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),

    # Rate Limit Config (ClickUp-specific)
    "RATE_LIMIT_PER_MIN": 100,  # Free/Unlimited plan; 1000 for Business+
}

# Convenience: ClickUp headers
# NOTE: ClickUp uses plain token auth (no "Bearer" prefix)
CLICKUP_HEADERS = {
    "Authorization": API["CLICKUP_TOKEN"] or "",
    "Content-Type": "application/json",
}

GROK_HEADERS = {
    "Authorization": f"Bearer {API['GROK_API_KEY']}",
    "Content-Type": "application/json",
}


# =============================================================================
# TEAM MEMBERS
# =============================================================================
# ClickUp uses integer user IDs (not string GIDs like Asana).
# Get member IDs via GET /api/v2/team/{team_id}/member
#
# "capacity" = max weekly allocation percentage (100% = full time)

TEAM = {
    # --- Video Studio ---
    "Zach Welliver": {
        "id": None,  # Set after GET /team/{id}/member
        "capacity": 100,
        "function": "Video",
        "lists": ["Preproduction"],
        "emails": [
            "zachw@perimeter.org",
            "zach.welliver@perimeter.org",
            "zwelliver@perimeter.org",
        ],
    },
    "Nick Clark": {
        "id": None,
        "capacity": 100,
        "function": "Video",
        "lists": ["Production"],
        "emails": [
            "nickc@perimeter.org",
            "nick.clark@perimeter.org",
        ],
    },
    "Adriel Abella": {
        "id": None,
        "capacity": 100,
        "function": "Video",
        "lists": ["Post Production"],
        "emails": [
            "adriela@perimeter.org",
            "adriel.abella@perimeter.org",
        ],
    },
    "John Meyer": {
        "id": None,
        "capacity": 30,
        "function": "Video",
        "lists": ["Preproduction", "Production", "Post Production"],
        "emails": [
            "johnm@perimeter.org",
            "john.meyer@perimeter.org",
        ],
    },

    # --- Graphic Design ---
    "David Tagg": {
        "id": None,
        "capacity": 100,
        "function": "Design",
        "lists": ["Design Pipeline"],
        "emails": [],
    },

    # --- Digital / Web & Social Media ---
    "Debbie Mason": {
        "id": None,
        "capacity": 100,
        "function": "Web/Social",
        "lists": ["Social Media Content Calendar", "Websites"],
        "emails": [],
    },

    # --- Photography ---
    "Katie Jean-Rejouis": {
        "id": None,
        "capacity": 100,
        "function": "Photo",
        "lists": ["Photo Capture Requests"],
        "emails": [],
    },

    # --- Project Managers ---
    "Jennifer Lee": {
        "id": None,
        "capacity": 100,
        "function": "PM",
        "lists": ["Comm Projects"],
        "emails": [],
    },
    "Darin Jameson": {
        "id": None,
        "capacity": 100,
        "function": "PM",
        "lists": ["Comm Projects"],
        "emails": [],
    },
    "Alexandra Shalikashvili": {
        "id": None,
        "capacity": 100,
        "function": "PM",
        "lists": ["Comm Projects"],
        "emails": [],
    },
    "Cammy Young": {
        "id": None,
        "capacity": 100,
        "function": "PM",
        "lists": ["Comm Projects"],
        "emails": [],
    },
}

# Studio shared email addresses (used for calendar event filtering)
STUDIO_EMAILS = [
    "comstudio@perimeter.org",
    "perimetercomstudio@gmail.com",
]

ALL_STUDIO_EMAILS = STUDIO_EMAILS.copy()
for member in TEAM.values():
    ALL_STUDIO_EMAILS.extend(member.get("emails", []))


# =============================================================================
# CLICKUP SPACES
# =============================================================================
# Spaces replace Asana Teams. One Space per department function.
# Get IDs via GET /api/v2/team/{team_id}/space

SPACES = {
    "Communications": "<SPACE_ID>",  # Main department space
    # Could also have separate spaces per function if preferred:
    # "Video Studio": "<SPACE_ID>",
    # "Design": "<SPACE_ID>",
}


# =============================================================================
# CLICKUP FOLDERS  (optional grouping inside Spaces)
# =============================================================================
# Folders replace the concept of grouping Asana projects by function.
# Get IDs via GET /api/v2/space/{space_id}/folder

FOLDERS = {
    "Video": "<FOLDER_ID>",        # Contains: Preproduction, Production, Post Production, Forecast
    "Design": "<FOLDER_ID>",       # Contains: Design Pipeline
    "Social": "<FOLDER_ID>",       # Contains: Social Media Content Calendar
    "Photo": "<FOLDER_ID>",        # Contains: Photo Capture Requests
    "Print": "<FOLDER_ID>",        # Contains: Print Production
    "Web": "<FOLDER_ID>",          # Contains: Websites
    "Campaigns": "<FOLDER_ID>",    # Contains: Holy Week 2026, Rush 2026, etc.
    "PM": "<FOLDER_ID>",           # Contains: Comm Projects
}


# =============================================================================
# CLICKUP LISTS  (equivalent to Asana Projects)
# =============================================================================
# Lists are where tasks live. Each List has its own set of Statuses.
# Get IDs via GET /api/v2/folder/{folder_id}/list
#
# NOTE: In ClickUp, tasks are created via POST /api/v2/list/{list_id}/task

LISTS = {
    # --- Video Studio ---
    "Video": {
        "Preproduction":    "<LIST_ID>",
        "Production":       "<LIST_ID>",
        "Post Production":  "<LIST_ID>",
        "Forecast":         "<LIST_ID>",
    },

    # --- Video External ---
    "Video External": {
        "Contracted/Outsourced": "<LIST_ID>",
    },

    # --- Video Supporting ---
    "Video Support": {
        "Video Project Overview": "<LIST_ID>",
        "Video Brief":            "<LIST_ID>",
    },

    # --- Communications ---
    "Communications": {
        "Comm Projects":            "<LIST_ID>",
        "COMMS REQUEST FORM":       "<LIST_ID>",
        "PLAYGROUND Comm Projects": "<LIST_ID>",
    },

    # --- Social Media ---
    "Social": {
        "Social Media Content Calendar": "<LIST_ID>",
    },

    # --- Photography ---
    "Photo": {
        "Photo Capture Requests": "<LIST_ID>",
    },

    # --- Design ---
    "Design": {
        "Design Pipeline": "<LIST_ID>",
    },

    # --- Print ---
    "Print": {
        "Print Production": "<LIST_ID>",
    },

    # --- Web ---
    "Web": {
        "Websites": "<LIST_ID>",
    },

    # --- Campaigns ---
    "Campaigns": {
        "Holy Week 2026": "<LIST_ID>",
        "Rush 2026":      "<LIST_ID>",
    },
}

# Flat lookup: list name -> ID (backward compatibility)
LIST_IDS = {}
for category in LISTS.values():
    LIST_IDS.update(category)

# Aliases for video scripts
VIDEO_LIST_IDS = LISTS["Video"]
EXTERNAL_LIST_IDS = LISTS["Video External"]


# =============================================================================
# CLICKUP STATUSES  (equivalent to Asana Sections)
# =============================================================================
# In ClickUp, each List has its own set of Statuses that tasks move through.
# Statuses are configured per-List in ClickUp settings (not via IDs like Asana sections).
# The scorer moves tasks between statuses using the task update endpoint.
#
# NOTE: ClickUp statuses are referenced by NAME (lowercase), not by GID.
# To update: PUT /api/v2/task/{task_id} with { "status": "in progress" }

STATUSES = {
    "Video Project Overview": [
        "complete the video brief",
        "video project requests",
        "preproduction - brief completed",
    ],
    "Social Media Content Calendar": [
        "idea/requested",
        "assigned/in progress",
        "review/revise",
        "approved for scheduling",
        "completed/scheduled",
        "stories form - debbie review",
        "archives",
    ],
    "Comm Projects": [
        "incoming",
        "assigned",
        "in progress",
        "in review",
        "complete",
    ],
    "Design Pipeline": [
        "requested",
        "concepting",
        "design",
        "review",
        "revisions",
        "final",
    ],
    "Print Production": [
        "requested",
        "design",
        "proof",
        "at vendor",
        "delivered",
    ],
}


# =============================================================================
# CLICKUP CUSTOM FIELDS
# =============================================================================
# Custom fields in ClickUp are created at the List level (or Space level if shared).
# Get field IDs via GET /api/v2/list/{list_id}/field
#
# IMPORTANT: Custom field values are SET via a dedicated endpoint:
#   POST /api/v2/task/{task_id}/field/{field_id}
#   Body: { "value": <value> }
#
# This is different from Asana where you can set custom fields on task create/update.
# For dropdown fields, "value" must be the option UUID from type_config.options

FIELDS = {
    # --- Scoring Fields (written by AI scorer) ---
    "Priority Score": {
        "id": "<FIELD_ID>",
        "type": "number",
    },
    "Complexity": {
        "id": "<FIELD_ID>",
        "type": "number",
    },
    "% Allocation": {
        "id": "<FIELD_ID>",
        "type": "number",
    },
    "Actual Allocation": {
        "id": "<FIELD_ID>",
        "type": "number",
    },

    # --- Dropdown Fields ---
    "Category": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Spiritual Formation": "<OPTION_UUID>",
            "Communications":     "<OPTION_UUID>",
            "Pastoral/Strategic":  "<OPTION_UUID>",
            "Partners":            "<OPTION_UUID>",
            "Creative Resources":  "<OPTION_UUID>",
        },
    },
    "Type": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Equipping":        "<OPTION_UUID>",
            "Enriching":        "<OPTION_UUID>",
            "Ministry Support": "<OPTION_UUID>",
            "Partner Support":  "<OPTION_UUID>",
        },
    },
    "Work Type": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Video":    "<OPTION_UUID>",
            "Design":   "<OPTION_UUID>",
            "Social":   "<OPTION_UUID>",
            "Photo":    "<OPTION_UUID>",
            "Print":    "<OPTION_UUID>",
            "Web":      "<OPTION_UUID>",
            "Campaign": "<OPTION_UUID>",
        },
    },
    "Task Progress": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Scheduled": "<OPTION_UUID>",
        },
    },
    "Approval": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Approved": "<OPTION_UUID>",
        },
    },
    "Forecast Status": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {
            "Pipeline":                "<OPTION_UUID>",
            "Ready for Preproduction": "<OPTION_UUID>",
            "On Hold":                 "<OPTION_UUID>",
            "Cancelled":               "<OPTION_UUID>",
        },
    },
    "Requesting Ministry": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
        "options": {},  # Populate with ministry list
    },

    # --- Other Fields ---
    "Film Date": {
        "id": "<FIELD_ID>",
        "type": "date",
    },
    "Start Date": {
        "id": "<FIELD_ID>",
        "type": "date",
        # NOTE: ClickUp has native start_date on tasks, may not need custom field
    },
    "Videographer": {
        "id": "<FIELD_ID>",
        "type": "drop_down",
    },
    "Virtual Location": {
        "id": "<FIELD_ID>",
        "type": "short_text",
    },
}

# Shortcut accessors (backward compatibility)
PERCENT_ALLOCATION_FIELD_ID = FIELDS["% Allocation"]["id"]
ACTUAL_ALLOCATION_FIELD_ID = FIELDS["Actual Allocation"]["id"]
PRIORITY_SCORE_FIELD_ID = FIELDS["Priority Score"]["id"]
COMPLEXITY_FIELD_ID = FIELDS["Complexity"]["id"]
CATEGORY_FIELD_ID = FIELDS["Category"]["id"]
TYPE_FIELD_ID = FIELDS["Type"]["id"]
FILM_DATE_FIELD_ID = FIELDS["Film Date"]["id"]
VIDEOGRAPHER_FIELD_ID = FIELDS["Videographer"]["id"]
VIRTUAL_LOCATION_FIELD_ID = FIELDS["Virtual Location"]["id"]


# =============================================================================
# SCORING CONFIGURATION  (identical to Asana version - scoring is PM-agnostic)
# =============================================================================

SCORING = {
    # --- Allocation Formula Constants ---
    "BASE_MULTIPLIER": 3.5,
    "PRIORITY_FLOOR": 0.5,
    "PRIORITY_DIVISOR": 24,
    "MIN_ALLOCATION": 5.0,
    "MAX_ALLOCATION": 80.0,
    "MIN_DURATION_WEEKS": 0.5,
    "DEFAULT_DURATION_DAYS": 30,
    "BROLL_MULTIPLIER": 1.5,

    # --- Phase Multipliers ---
    "PHASE_MULTIPLIERS": {
        "Video": {
            "Preproduction":  0.8,
            "Production":     1.2,
            "Post Production": 2.0,
        },
        "Design": {
            "Concepting":     0.6,
            "Design":         1.0,
            "Review":         0.8,
        },
        "Social": {
            "Planning":       0.5,
            "Creation":       1.0,
            "Scheduling":     0.3,
        },
        "Photo": {
            "Planning":       0.4,
            "Shoot":          1.5,
            "Editing":        1.0,
        },
        "Print": {
            "Design":         0.8,
            "Proofing":       0.4,
            "Vendor":         0.3,
        },
        "Web": {
            "Planning":       0.6,
            "Development":    1.2,
            "Testing":        0.5,
        },
    },

    "PHASE_WEIGHTS": {
        "Pre": 0.25,
        "Production": 0.25,
        "Post": 0.50,
    },

    "CATEGORY_TARGETS": {
        "Spiritual Formation": 0.25,
        "Communications":      0.30,
        "Creative Resources":  0.15,
        "Pastoral/Strategic":  0.20,
        "Partners":            0.05,
    },

    "ACCURACY_THRESHOLDS": {
        "accurate":   0.10,
        "moderate":   0.25,
    },

    "DELIVERY_THRESHOLDS": {
        "on_time":        0,
        "slightly_late":  2,
    },

    "ALLOCATION_VARIANCE_TOLERANCE": 2.0,
    "MAX_CONCURRENT_TASKS": 5,
}

# Backward-compatible flat shortcuts
PHASE_MULTIPLIERS = SCORING["PHASE_MULTIPLIERS"]["Video"]
PHASE_WEIGHTS = SCORING["PHASE_WEIGHTS"]
TARGETS = SCORING["CATEGORY_TARGETS"]


# =============================================================================
# ALERTS & NOTIFICATIONS  (identical to Asana version)
# =============================================================================

ALERTS = {
    "ALERT_EMAIL_FROM": os.getenv("ALERT_EMAIL_FROM", "studio@perimeter.org"),
    "ALERT_EMAIL_TO": os.getenv("ALERT_EMAIL_TO", "zwelliver@perimeter.org"),
    "WEEKLY_REPORT_TO": "zwelliver@perimeter.org",

    "SLACK_WEBHOOK_CAPACITY": os.getenv("SLACK_WEBHOOK_CAPACITY"),

    "CAPACITY_OVER": 1.00,
    "CAPACITY_NEAR_LIMIT": 0.90,
    "CAPACITY_HIGH": 0.75,

    "FORECAST_ALERT_DAYS": 30,
    "STALE_TASK_DAYS": 7,

    "WOV_ALERT_DAY": "Wednesday",
    "WOV_ALERT_HOUR": 16,

    "FEEDBACK_RECIPIENT": "Zach",
    "FEEDBACK_LOOKBACK_DAYS": 7,
}


# =============================================================================
# GOOGLE CALENDAR  (identical to Asana version - calendar sync is PM-agnostic)
# =============================================================================

CALENDAR = {
    "SCOPES": ["https://www.googleapis.com/auth/calendar.events"],
    "SCOPES_READONLY": ["https://www.googleapis.com/auth/calendar.readonly"],
    "CALENDAR_ID": "primary",
    "TOKEN_FILE": "token.pickle",
    "CREDENTIALS_FILE": "credentials.json",

    "COLOR_FILM_DATE": "7",
    "COLOR_DUE_DATE": "11",

    "DEFAULT_FILM_TIME": "09:00:00.000Z",
    "DEFAULT_DUE_TIME": "21:00:00.000Z",

    "REMINDER_EMAIL_MINUTES": 24 * 60,
    "REMINDER_POPUP_MINUTES": 60,

    "WOV_SEARCH_TERM": "WOV",
    "WOV_LOOKAHEAD_DAYS": 90,
    "WOV_VIRTUAL_LOCATION": "WOV Set",
    "WOV_EXCLUDED_PREFIXES": ["✅ DUE:", "✅ FILM:"],

    "FILM_MAPPING_FILE": "film_calendar_mapping.json",
    "DUE_MAPPING_FILE": "due_calendar_mapping.json",
    "WOV_MAPPING_FILE": "wov_calendar_mapping.json",
}


# =============================================================================
# FILE PATHS  (identical to Asana version)
# =============================================================================

BASE_DIR = os.path.expanduser("~/Scripts/StudioProcesses")

PATHS = {
    "BASE_DIR": BASE_DIR,
    "REPORTS_DIR": os.path.join(BASE_DIR, "Reports"),

    "SCORER_LOG": os.path.join(BASE_DIR, "video_scorer.log"),
    "COMM_SCORER_LOG": os.path.join(BASE_DIR, "comm_scorer.log"),
    "AUDIT_LOG": os.path.join(BASE_DIR, "manipulation_audit.log"),
    "SCORER_LAST_RUN": os.path.join(BASE_DIR, "last_run.txt"),
    "SCORER_PROCESSED": os.path.join(BASE_DIR, "scorer_processed.txt"),

    "CAPACITY_ALERTS_LOG": os.path.join(BASE_DIR, "capacity_alerts.txt"),
    "CAPACITY_HISTORY": os.path.join(BASE_DIR, "Reports", "capacity_history.csv"),
    "CAPACITY_FORECAST": os.path.join(BASE_DIR, "Reports", "capacity_forecast.csv"),
    "CAPACITY_COMBINED": os.path.join(BASE_DIR, "Reports", "capacity_combined.csv"),

    "DELIVERY_LOG": os.path.join(BASE_DIR, "Reports", "delivery_performance_log.csv"),
    "DELIVERY_SUMMARY": os.path.join(BASE_DIR, "Reports", "delivery_performance_summary.csv"),

    "ALLOCATION_REPORT": os.path.join(BASE_DIR, "Reports", "weighted_allocation_report.csv"),
    "VARIANCE_HISTORY": os.path.join(BASE_DIR, "Reports", "variance_tracking_history.csv"),

    "FORECAST_MATCHER_LOG": os.path.join(BASE_DIR, "forecast_matcher.log"),
    "FORECAST_MATCHER_STATE": os.path.join(BASE_DIR, "forecast_matcher_processed.json"),

    "TIMELINE_PROCESSED": os.path.join(BASE_DIR, "processed_timeline.txt"),

    "BACKDROP_LAST_RUN": os.path.join(BASE_DIR, "production_last_run.txt"),
    "BACKDROP_SYNC_TOKEN": os.path.join(BASE_DIR, "production_sync_token.txt"),
    "BACKDROP_PROCESSED": os.path.join(BASE_DIR, "processed_backdrops.txt"),

    "FEEDBACK_STATE": os.path.join(BASE_DIR, "feedback_posted_tasks.json"),
}


# =============================================================================
# FORECAST MATCHING  (identical to Asana version)
# =============================================================================

FORECAST = {
    "HIGH_CONFIDENCE": 0.80,
    "MEDIUM_CONFIDENCE": 0.50,
    "WEIGHTS": {
        "name_similarity":   0.50,
        "date_proximity":    0.25,
        "ministry_match":    0.15,
        "stakeholder_match": 0.10,
    },
    "MINISTRY_KEYWORDS": [
        "global", "outreach", "women", "men", "student", "children",
        "kids", "generosity", "frontier", "discipleship", "belong",
        "life on life", "lol", "camp", "worship", "communications",
        "comm", "pastoral",
    ],
}


# =============================================================================
# BRAND / UI COLORS  (identical to Asana version)
# =============================================================================

BRAND = {
    "NAVY":       "#09243F",
    "BLUE":       "#60BBE9",
    "OFF_WHITE":  "#f8f9fa",
    "LIGHT_NAVY": "#4a5f7f",
    "HEATMAP_COLORS": ["#e8f5e9", "#81c784", "#ffd54f", "#ff8a65", "#ef5350"],
    "BORDER_GRAY": "#ecf0f1",
}


# =============================================================================
# IMAGE GENERATION  (identical to Asana version)
# =============================================================================

BACKDROPS = {
    "REPLICATE_ASPECT_RATIO": "16:9",
    "REPLICATE_FORMAT": "png",
    "REPLICATE_QUALITY": 100,
    "REPLICATE_SAFETY": 2,
    "SD_ASPECT_RATIO": "21:9",
    "SD_FORMAT": "png",
}


# =============================================================================
# REPORT GENERATION  (identical to Asana version)
# =============================================================================

REPORTS = {
    "HEATMAP_MONTHS_BACK": 2,
    "HEATMAP_MONTHS_FORWARD": 10,
    "HEATMAP_FIGSIZE": (24, 10),
    "HEATMAP_DPI": 150,
    "HEATMAP_GRID": (4, 3),

    "CAPACITY_HISTORY_DAYS": 30,
    "FORECAST_DAYS_FORWARD": 60,

    "EXTERNAL_TASK_LIMIT": 5,
    "UPCOMING_SHOOTS_LIMIT": 10,
    "UPCOMING_DEADLINES_DAYS": 10,
}


# =============================================================================
# CLICKUP-SPECIFIC: API HELPER PATTERNS
# =============================================================================
# These patterns document how ClickUp API calls differ from Asana.
# Included here for reference when migrating scripts.

API_PATTERNS = {
    "get_tasks": "GET /api/v2/list/{list_id}/task?include_closed=true",
    "get_task": "GET /api/v2/task/{task_id}?custom_fields=true",
    "create_task": "POST /api/v2/list/{list_id}/task",
    "update_task": "PUT /api/v2/task/{task_id}",
    "set_custom_field": "POST /api/v2/task/{task_id}/field/{field_id}",
    "get_list_fields": "GET /api/v2/list/{list_id}/field",
    "get_members": "GET /api/v2/team/{team_id}/member",  # NOTE: "team" = workspace
    "get_spaces": "GET /api/v2/team/{team_id}/space",
    "get_folders": "GET /api/v2/space/{space_id}/folder",
    "get_lists": "GET /api/v2/folder/{folder_id}/list",
    "search_tasks": "GET /api/v2/team/{team_id}/task?search={query}",
    "create_webhook": "POST /api/v2/team/{team_id}/webhook",
}

# Mapping: Asana API pattern → ClickUp equivalent (for migration reference)
MIGRATION_MAP = {
    # Asana                          →  ClickUp
    # GET  /tasks/{task_gid}         →  GET  /task/{task_id}
    # PUT  /tasks/{task_gid}         →  PUT  /task/{task_id}
    # POST /tasks (with project)     →  POST /list/{list_id}/task
    # GET  /projects/{gid}/tasks     →  GET  /list/{list_id}/task
    # GET  /projects/{gid}/sections  →  (statuses are on the List itself)
    # PUT  /tasks/{gid} custom_fields→  POST /task/{task_id}/field/{field_id}
    # GET  /workspaces               →  GET  /team
    # GET  /projects                 →  GET  /folder/{id}/list or /space/{id}/list
}


# =============================================================================
# COMPUTED VALUES
# =============================================================================

def get_team_by_function(function_name):
    """Get all team members for a given function (Video, Design, Web/Social, etc.)"""
    return {
        name: info for name, info in TEAM.items()
        if info["function"] == function_name
    }

def get_max_capacity(function_name=None):
    """Calculate total max capacity, optionally filtered by function"""
    members = TEAM.values() if not function_name else get_team_by_function(function_name).values()
    return sum(m["capacity"] for m in members)

def get_member_by_id(member_id):
    """Look up a team member by their ClickUp user ID"""
    for name, info in TEAM.items():
        if info["id"] == member_id:
            return name, info
    return None, None

def get_list_id(category, name):
    """Get a List ID by category and name"""
    return LISTS.get(category, {}).get(name)

def get_phase_multiplier(work_type, phase_name):
    """Get the phase multiplier for a work type and phase"""
    return SCORING["PHASE_MULTIPLIERS"].get(work_type, {}).get(phase_name, 1.0)


# Legacy computed values
MAX_CAPACITY = get_max_capacity("Video")
