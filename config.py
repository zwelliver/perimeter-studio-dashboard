"""
Perimeter Church Communications Department - Centralized Configuration
======================================================================

Single source of truth for all automation scripts. Every script imports
from here instead of hardcoding GIDs, team members, API settings, etc.

Usage in any script:
    from config import CONFIG, TEAM, PROJECTS, FIELDS, SCORING, ALERTS, PATHS

Maintained by: Zach Welliver
Last updated: 2026-02-06
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


# =============================================================================
# WORKSPACE
# =============================================================================

WORKSPACE_GID = "12090996748128"  # perimeter.org


# =============================================================================
# API CREDENTIALS (all from .env - never hardcode secrets)
# =============================================================================

API = {
    # Asana
    "ASANA_PAT_SCORER": os.getenv("ASANA_PAT_SCORER"),
    "ASANA_PAT_BACKDROP": os.getenv("ASANA_PAT_BACKDROP"),
    "ASANA_BASE_URL": "https://app.asana.com/api/1.0",

    # Grok (xAI)
    "GROK_API_KEY": os.getenv("GROK_API_KEY"),
    "GROK_ENDPOINT": "https://api.x.ai/v1/chat/completions",
    "GROK_MODEL": "grok-4-fast-non-reasoning",
    "GROK_MODEL_ANALYSIS": "grok-beta",  # Used for post-completion analysis

    # Image Generation
    "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN"),
    "REPLICATE_MODEL": "black-forest-labs/flux-2-max",
    "SD_API_KEY": os.getenv("STABLE_DIFFUSION_API_KEY"),
    "SD_ENDPOINT": "https://api.stability.ai/v2beta/stable-image/generate/ultra",

    # Email / SMTP
    "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")),
    "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
    "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
}

# Convenience: Asana headers (most scripts need these)
ASANA_HEADERS = {
    "Authorization": f"Bearer {API['ASANA_PAT_SCORER']}",
    "Content-Type": "application/json"
}

ASANA_HEADERS_BACKDROP = {
    "Authorization": f"Bearer {API['ASANA_PAT_BACKDROP']}",
    "Content-Type": "application/json"
}

GROK_HEADERS = {
    "Authorization": f"Bearer {API['GROK_API_KEY']}",
    "Content-Type": "application/json"
}


# =============================================================================
# TEAM MEMBERS
# =============================================================================
# Each member has: gid, capacity (%), function, projects, email aliases
# "capacity" = max weekly allocation percentage (100% = full time)

TEAM = {
    # --- Video Studio ---
    "Zach Welliver": {
        "gid": "1205076276256605",
        "capacity": 100,
        "function": "Video",
        "projects": ["Preproduction"],
        "emails": [
            "zachw@perimeter.org",
            "zach.welliver@perimeter.org",
            "zwelliver@perimeter.org",
        ],
    },
    "Nick Clark": {
        "gid": "1202206953008470",
        "capacity": 100,
        "function": "Video",
        "projects": ["Production"],
        "emails": [
            "nickc@perimeter.org",
            "nick.clark@perimeter.org",
        ],
    },
    "Adriel Abella": {
        "gid": "1208249805795150",
        "capacity": 100,
        "function": "Video",
        "projects": ["Post Production"],
        "emails": [
            "adriela@perimeter.org",
            "adriel.abella@perimeter.org",
        ],
    },
    "John Meyer": {
        "gid": "1211292436943049",
        "capacity": 30,
        "function": "Video",
        "projects": ["Preproduction", "Production", "Post Production"],
        "emails": [
            "johnm@perimeter.org",
            "john.meyer@perimeter.org",
        ],
    },

    # --- Graphic Design ---
    "David Tagg": {
        "gid": "1202125922693650",
        "capacity": 100,
        "function": "Design",
        "projects": ["Design Pipeline"],
        "emails": [],
    },

    # --- Digital / Web & Social Media ---
    "Debbie Mason": {
        "gid": "1202477066116879",
        "capacity": 100,
        "function": "Web/Social",
        "projects": ["Social Media Content Calendar", "Websites"],
        "emails": [],
    },

    # --- Photography ---
    "Katie Jean-Rejouis": {
        "gid": "1204082772133733",
        "capacity": 100,
        "function": "Photo",
        "projects": ["Photo Capture Requests"],
        "emails": [],
    },

    # --- Project Managers ---
    "Jennifer Lee": {
        "gid": "1198956584344676",
        "capacity": 100,
        "function": "PM",
        "projects": ["Comm Projects"],
        "emails": [],
    },
    "Darin Jameson": {
        "gid": "1150280469992906",
        "capacity": 100,
        "function": "PM",
        "projects": ["Comm Projects"],
        "emails": [],
    },
    "Alexandra Shalikashvili": {
        "gid": "1208249690115699",
        "capacity": 100,
        "function": "PM",
        "projects": ["Comm Projects"],
        "emails": [],
    },
    "Cammy Young": {
        "gid": "1210967811291482",
        "capacity": 100,
        "function": "PM",
        "projects": ["Comm Projects"],
        "emails": [],
    },
}

# Studio shared email addresses (used for calendar event filtering)
STUDIO_EMAILS = [
    "comstudio@perimeter.org",
    "perimetercomstudio@gmail.com",
]

# Build all known emails (studio + individual) for calendar matching
ALL_STUDIO_EMAILS = STUDIO_EMAILS.copy()
for member in TEAM.values():
    ALL_STUDIO_EMAILS.extend(member.get("emails", []))


# =============================================================================
# ASANA PROJECTS
# =============================================================================

PROJECTS = {
    # --- Video Studio (existing) ---
    "Video": {
        "Preproduction":    "1208336083003480",
        "Production":       "1209597979075357",
        "Post Production":  "1209581743268502",
        "Forecast":         "1212059678473189",
    },

    # --- Video External (tracking only, not scored) ---
    "Video External": {
        "Contracted/Outsourced": "1212319598244265",
    },

    # --- Video Supporting ---
    "Video Support": {
        "Video Project Overview": "1209792136396083",
        "Video Brief":            "1208059775360686",
    },

    # --- Communications (existing) ---
    "Communications": {
        "Comm Projects":            "1208320234465789",
        "COMMS REQUEST FORM":       "1210822904116413",
        "PLAYGROUND Comm Projects":  "1212962225910405",
    },

    # --- Social Media (existing) ---
    "Social": {
        "Social Media Content Calendar": "1202594716577348",
    },

    # --- Photography (existing) ---
    "Photo": {
        "Photo Capture Requests": "1208320234465801",
    },

    # --- Design (to be created in Phase 1) ---
    "Design": {
        # "Design Pipeline": "<GID>",  # Uncomment when created
    },

    # --- Print (to be created in Phase 1) ---
    "Print": {
        # "Print Production": "<GID>",  # Uncomment when created
    },

    # --- Web (existing) ---
    "Web": {
        # Add web project GIDs when integrated
    },

    # --- Campaigns (existing, per-event) ---
    "Campaigns": {
        "Holy Week 2026":  "1212722654697974",
        "Rush 2026":       "1211903063537945",
    },
}

# Flat lookup: project name -> GID (for backward compatibility)
PROJECT_GIDS = {}
for category in PROJECTS.values():
    PROJECT_GIDS.update(category)

# Video-specific shortcuts (used by video_scorer.py, dashboard, etc.)
VIDEO_PROJECT_GIDS = PROJECTS["Video"]
EXTERNAL_PROJECT_GIDS = PROJECTS["Video External"]


# =============================================================================
# ASANA SECTION GIDS
# =============================================================================

SECTIONS = {
    "Video Project Overview": {
        "Complete the Video Brief":           "1212821259992499",
        "Video Project Requests":             "1209792136396084",
        "Preproduction - Brief Completed":    "1209802507784567",
    },
    "Social Media Content Calendar": {
        "Idea/Requested":                     "1212693011146032",
        "Assigned/In Progress":               "1210393278284839",
        "Review/Revise":                      "1210732871445815",
        "Approved for Scheduling":            "1212693011146033",
        "Completed/Scheduled":                "1212693011146029",
        "Stories Form - Debbie Review":       "1202594716577349",
        "Archives":                           "1208343259490409",
    },
}


# =============================================================================
# ASANA CUSTOM FIELDS
# =============================================================================

FIELDS = {
    # --- Scoring Fields (written by AI scorer) ---
    "Priority Score": {
        "gid": "1209600375748352",
        "type": "number",
    },
    "Complexity": {
        "gid": "1209600375748350",
        "type": "number",
    },
    "% Allocation": {
        "gid": "1208923995383367",
        "type": "number",
    },
    "Actual Allocation": {
        "gid": "1212060330747288",
        "type": "number",
    },

    # --- Enum Fields ---
    "Category": {
        "gid": "1211901611025610",
        "type": "enum",
        "options": {
            "Spiritual Formation": "1211901611025611",
            "Communications":     "1211901611025612",
            "Pastoral/Strategic":  "1211901611025613",
            "Partners":            "1211901611025614",
            "Creative Resources":  "1211901611025615",
        },
    },
    "Type": {
        "gid": "1209581743268525",
        "type": "enum",
        "options": {
            "Equipping":        "1209581744608310",
            "Enriching":        "1209581744608311",
            "Ministry Support": "1209581744608312",
            "Partner Support":  "1209581744608313",
        },
    },
    "Task Progress": {
        "gid": "1209598240843051",
        "type": "enum",
        "options": {
            "Scheduled":     "1209598240843053",
            # Add other options as needed
        },
    },
    "Approval": {
        "gid": "1209632867555289",
        "type": "enum",
        "options": {
            "Approved": "1209632867555292",
        },
    },
    "Forecast Status": {
        "gid": None,  # Set after setup_forecast_status_field.py creates it
        "type": "enum",
        "options": {
            "Pipeline":                  None,
            "Ready for Preproduction":   None,
            "On Hold":                   None,
            "Cancelled":                 None,
        },
    },

    # --- Other Fields ---
    "Film Date": {
        "gid": "1212211613150378",
        "type": "date",
    },
    "Start Date": {
        "gid": "1211967927674488",
        "type": "date",
    },
    "Videographer": {
        "gid": "1209693890455555",
        "type": "enum",
    },
    "Virtual Location": {
        "gid": "1209661703587753",
        "type": "text",
    },
}

# Shortcut GID accessors (backward compatibility for existing scripts)
PERCENT_ALLOCATION_FIELD_GID = FIELDS["% Allocation"]["gid"]
ACTUAL_ALLOCATION_FIELD_GID = FIELDS["Actual Allocation"]["gid"]
PRIORITY_SCORE_FIELD_GID = FIELDS["Priority Score"]["gid"]
COMPLEXITY_FIELD_GID = FIELDS["Complexity"]["gid"]
CATEGORY_FIELD_GID = FIELDS["Category"]["gid"]
TYPE_FIELD_GID = FIELDS["Type"]["gid"]
FILM_DATE_FIELD_GID = FIELDS["Film Date"]["gid"]
START_DATE_FIELD_GID = FIELDS["Start Date"]["gid"]
TASK_PROGRESS_FIELD_GID = FIELDS["Task Progress"]["gid"]
APPROVAL_FIELD_GID = FIELDS["Approval"]["gid"]
VIDEOGRAPHER_FIELD_GID = FIELDS["Videographer"]["gid"]
VIRTUAL_LOCATION_FIELD_GID = FIELDS["Virtual Location"]["gid"]

# Enum option GID shortcuts
CATEGORY_OPTION_GIDS = FIELDS["Category"]["options"]
TYPE_OPTION_GIDS = FIELDS["Type"]["options"]


# =============================================================================
# SCORING CONFIGURATION
# =============================================================================

SCORING = {
    # --- Allocation Formula Constants ---
    "BASE_MULTIPLIER": 3.5,            # Complexity * this = base allocation
    "PRIORITY_FLOOR": 0.5,             # Minimum priority factor
    "PRIORITY_DIVISOR": 24,            # Priority / this = priority boost
    "MIN_ALLOCATION": 5.0,             # Floor: no task is less than 5%
    "MAX_ALLOCATION": 80.0,            # Cap: no task exceeds 80%
    "MIN_DURATION_WEEKS": 0.5,         # Minimum task duration for calc
    "DEFAULT_DURATION_DAYS": 30,       # When due date is missing
    "BROLL_MULTIPLIER": 1.5,           # Applied to Production phase when B-roll

    # --- Phase Multipliers (effort weight per production phase) ---
    "PHASE_MULTIPLIERS": {
        "Video": {
            "Preproduction":  0.8,     # Planning, scripting
            "Production":     1.2,     # Filming, recording
            "Post Production": 2.0,    # Editing, revisions
        },
        "Design": {
            "Concepting":     0.6,     # Research, mood boards
            "Design":         1.0,     # Core creative work
            "Review":         0.8,     # Stakeholder feedback
        },
        "Social": {
            "Planning":       0.5,     # Calendar, copy writing
            "Creation":       1.0,     # Asset creation
            "Scheduling":     0.3,     # Platform scheduling
        },
        "Photo": {
            "Planning":       0.4,     # Shot lists, scouting
            "Shoot":          1.5,     # On-site photography
            "Editing":        1.0,     # Culling, retouching
        },
        "Print": {
            "Design":         0.8,     # Print-specific layout
            "Proofing":       0.4,     # Proof review cycles
            "Vendor":         0.3,     # Vendor coordination
        },
        "Web": {
            "Planning":       0.6,     # Wireframes, content
            "Development":    1.2,     # Build, integration
            "Testing":        0.5,     # QA, launch
        },
    },

    # --- Phase Weights (for heatmap generation) ---
    "PHASE_WEIGHTS": {
        "Pre": 0.25,
        "Production": 0.25,
        "Post": 0.50,
    },

    # --- Category Allocation Targets ---
    "CATEGORY_TARGETS": {
        "Spiritual Formation": 0.25,
        "Communications":      0.30,
        "Creative Resources":  0.15,
        "Pastoral/Strategic":  0.20,
        "Partners":            0.05,
    },

    # --- Allocation Accuracy Thresholds ---
    "ACCURACY_THRESHOLDS": {
        "accurate":   0.10,            # <= 10% variance
        "moderate":   0.25,            # <= 25% variance
        # > 25% = "Significant Variance"
    },

    # --- Delivery Timing Thresholds (days) ---
    "DELIVERY_THRESHOLDS": {
        "on_time":        0,           # <= 0 days late
        "slightly_late":  2,           # <= 2 days late
        # > 2 = "Late"
    },

    # --- Variance Tolerance (allocation) ---
    "ALLOCATION_VARIANCE_TOLERANCE": 2.0,  # ±2%

    # --- Concurrent processing ---
    "MAX_CONCURRENT_TASKS": 5,
}

# Backward-compatible flat shortcuts for video_scorer.py
PHASE_MULTIPLIERS = SCORING["PHASE_MULTIPLIERS"]["Video"]
PHASE_WEIGHTS = SCORING["PHASE_WEIGHTS"]
TARGETS = SCORING["CATEGORY_TARGETS"]


# =============================================================================
# ALERTS & NOTIFICATIONS
# =============================================================================

ALERTS = {
    # --- Email Recipients ---
    "ALERT_EMAIL_FROM": os.getenv("ALERT_EMAIL_FROM", "studio@perimeter.org"),
    "ALERT_EMAIL_TO": os.getenv("ALERT_EMAIL_TO", "zwelliver@perimeter.org"),
    "WEEKLY_REPORT_TO": "zwelliver@perimeter.org",

    # --- Slack ---
    "SLACK_WEBHOOK_CAPACITY": os.getenv("SLACK_WEBHOOK_CAPACITY"),

    # --- Capacity Thresholds ---
    "CAPACITY_OVER": 1.00,             # > 100% = over capacity
    "CAPACITY_NEAR_LIMIT": 0.90,       # > 90% = near limit
    "CAPACITY_HIGH": 0.75,             # > 75% = high utilization

    # --- Forecast Pipeline ---
    "FORECAST_ALERT_DAYS": 30,         # Alert when forecast item is within 30 days
    "STALE_TASK_DAYS": 7,              # Flag tasks with no update for 7+ days

    # --- WOV ---
    "WOV_ALERT_DAY": "Wednesday",
    "WOV_ALERT_HOUR": 16,              # 4:00 PM

    # --- Post-Completion Feedback ---
    "FEEDBACK_RECIPIENT": "Zach",
    "FEEDBACK_LOOKBACK_DAYS": 7,

    # --- Scheduling Conflict Alerts ---
    "SLACK_WEBHOOK_CONFLICTS": os.getenv("SLACK_WEBHOOK_CONFLICTS", os.getenv("SLACK_WEBHOOK_CAPACITY", "")),
    "CONFLICT_COMPLEXITY_THRESHOLD": 7,  # Complexity >= this triggers same-day proximity warnings
}


# =============================================================================
# GOOGLE CALENDAR
# =============================================================================

CALENDAR = {
    "SCOPES": ["https://www.googleapis.com/auth/calendar.events"],
    "SCOPES_READONLY": ["https://www.googleapis.com/auth/calendar.readonly"],
    "CALENDAR_ID": "primary",
    "TOKEN_FILE": "token.pickle",
    "CREDENTIALS_FILE": "credentials.json",

    # --- Event Colors (Google Calendar color IDs) ---
    "COLOR_FILM_DATE": "7",            # Peacock (blue-teal)
    "COLOR_DUE_DATE": "11",            # Tomato (red)

    # --- Default Times ---
    "DEFAULT_FILM_TIME": "09:00:00.000Z",
    "DEFAULT_DUE_TIME": "21:00:00.000Z",  # 4:00 PM EST

    # --- Reminders ---
    "REMINDER_EMAIL_MINUTES": 24 * 60,    # 24 hours
    "REMINDER_POPUP_MINUTES": 60,          # 1 hour

    # --- WOV Calendar Settings ---
    "WOV_SEARCH_TERM": "WOV",
    "WOV_LOOKAHEAD_DAYS": 90,
    "WOV_VIRTUAL_LOCATION": "WOV Set",
    "WOV_EXCLUDED_PREFIXES": ["✅ DUE:", "✅ FILM:"],

    # --- Mapping Files ---
    "FILM_MAPPING_FILE": "film_calendar_mapping.json",
    "DUE_MAPPING_FILE": "due_calendar_mapping.json",
    "WOV_MAPPING_FILE": "wov_calendar_mapping.json",
}


# =============================================================================
# FILE PATHS
# =============================================================================

BASE_DIR = os.path.expanduser("~/Scripts/StudioProcesses")

PATHS = {
    "BASE_DIR": BASE_DIR,
    "REPORTS_DIR": os.path.join(BASE_DIR, "Reports"),

    # --- Scorer State Files ---
    "SCORER_LOG": os.path.join(BASE_DIR, "video_scorer.log"),
    "COMM_SCORER_LOG": os.path.join(BASE_DIR, "comm_scorer.log"),
    "AUDIT_LOG": os.path.join(BASE_DIR, "manipulation_audit.log"),
    "SCORER_LAST_RUN": os.path.join(BASE_DIR, "last_run.txt"),
    "SCORER_PROCESSED": os.path.join(BASE_DIR, "scorer_processed.txt"),

    # --- Capacity & Alerts ---
    "CAPACITY_ALERTS_LOG": os.path.join(BASE_DIR, "capacity_alerts.txt"),
    "CAPACITY_HISTORY": os.path.join(BASE_DIR, "Reports", "capacity_history.csv"),
    "CAPACITY_FORECAST": os.path.join(BASE_DIR, "Reports", "capacity_forecast.csv"),
    "CAPACITY_COMBINED": os.path.join(BASE_DIR, "Reports", "capacity_combined.csv"),

    # --- Delivery Performance ---
    "DELIVERY_LOG": os.path.join(BASE_DIR, "Reports", "delivery_performance_log.csv"),
    "DELIVERY_SUMMARY": os.path.join(BASE_DIR, "Reports", "delivery_performance_summary.csv"),

    # --- Allocation Reports ---
    "ALLOCATION_REPORT": os.path.join(BASE_DIR, "Reports", "weighted_allocation_report.csv"),
    "VARIANCE_HISTORY": os.path.join(BASE_DIR, "Reports", "variance_tracking_history.csv"),

    # --- Forecast ---
    "FORECAST_MATCHER_LOG": os.path.join(BASE_DIR, "forecast_matcher.log"),
    "FORECAST_MATCHER_STATE": os.path.join(BASE_DIR, "forecast_matcher_processed.json"),

    # --- Production Timeline ---
    "TIMELINE_PROCESSED": os.path.join(BASE_DIR, "processed_timeline.txt"),

    # --- Backdrops ---
    "BACKDROP_LAST_RUN": os.path.join(BASE_DIR, "production_last_run.txt"),
    "BACKDROP_SYNC_TOKEN": os.path.join(BASE_DIR, "production_sync_token.txt"),
    "BACKDROP_PROCESSED": os.path.join(BASE_DIR, "processed_backdrops.txt"),

    # --- Feedback ---
    "FEEDBACK_STATE": os.path.join(BASE_DIR, "feedback_posted_tasks.json"),

    # --- Scheduling Conflict Alerts ---
    "CONFLICT_ALERTS_LOG": os.path.join(BASE_DIR, "scheduling_conflict_alerts.txt"),
    "CONFLICT_ALERT_STATE": os.path.join(BASE_DIR, "scheduling_conflict_state.json"),
}


# =============================================================================
# PERIMETER CHURCH ACRONYMS
# =============================================================================
# Lookup dictionary for expanding church-specific acronyms in task names/
# descriptions before sending to AI scoring. The expand_acronyms() function
# below replaces acronyms with their full names for better scoring context.

ACRONYMS = {
    # --- Leadership & Governance ---
    "ELT":   "Executive Leadership Team",
    "EMT":   "Elder Ministry Team",
    "OLT":   "Operations Leadership Team",
    "OMT":   "Operations Management Team",
    "XP":    "Executive Pastor",
    "SSLT":  "Sermon Series Leadership Team",
    "SMT":   "School Ministry Team",
    "RE":    "Ruling Elder",
    "TE":    "Teaching Elder",

    # --- Ministries & Programs ---
    "LLM":   "Life on Life Ministries",
    "LOL":   "Life on Life Ministries",
    "MAS":   "Metro Atlanta Seminary",
    "PCA":   "Presbyterian Church in America",
    "MAP":   "Metro Atlanta Presbytery",
    "PCO":   "Planning Center Online",
    "GBI":   "Greet Befriend Invite",
    "KCP":   "Know Consider Present",
    "LDC":   "Lead Develop Care",

    # --- Events & Processes ---
    "MPKO":  "Ministry Planning Kickoff",
    "SDD":   "Staff Development Day",
    "GA":    "General Assembly",

    # --- Worship Service Elements ---
    "AOP":   "Assurance of Pardon",
    "BCO":   "Book of Church Order",
    "CTW":   "Call To Worship",
    "WL":    "Worship Leader",
    "WP":    "Worship Pastor",
    "WOV":   "Weekly Opportunity Video",

    # --- Education ---
    "DMin":  "Doctorate of Ministry",
    "MDiv":  "Masters of Divinity",
    "MA":    "Ministry Associate",

    # --- Perimeter-Specific Shorthand ---
    "CAA":   "Camp All-American",
    "OME":   "Outdoor Ministry Events",
    "DD":    "Digging Deeper",
}

def expand_acronyms(text):
    """Expand known Perimeter acronyms in a text string.

    Used before sending task names/descriptions to Grok for scoring.
    Only replaces whole-word matches to avoid false positives
    (e.g., won't replace 'TEAM' inside a longer word).

    Usage:
        from config import expand_acronyms
        expanded_name = expand_acronyms(task_name)
    """
    if not text:
        return text
    import re
    result = text
    for acronym, full_name in ACRONYMS.items():
        # Word-boundary match, case-sensitive
        pattern = r'\b' + re.escape(acronym) + r'\b'
        result = re.sub(pattern, f"{acronym} ({full_name})", result)
    return result


# =============================================================================
# FORECAST MATCHING
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
        "life on life", "lol", "llm", "camp", "worship", "communications",
        "comm", "pastoral", "elt", "sslt", "sdd", "mpko", "caa", "ome",
        "digging deeper", "dd", "wov", "mas", "pca",
    ],
}


# =============================================================================
# BRAND / UI COLORS
# =============================================================================

BRAND = {
    "NAVY":       "#09243F",
    "BLUE":       "#60BBE9",
    "OFF_WHITE":  "#f8f9fa",
    "LIGHT_NAVY": "#4a5f7f",

    # Heatmap gradient
    "HEATMAP_COLORS": ["#e8f5e9", "#81c784", "#ffd54f", "#ff8a65", "#ef5350"],

    # UI
    "BORDER_GRAY": "#ecf0f1",
}


# =============================================================================
# IMAGE GENERATION (Backdrops)
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
# REPORT GENERATION SETTINGS
# =============================================================================

REPORTS = {
    "HEATMAP_MONTHS_BACK": 2,
    "HEATMAP_MONTHS_FORWARD": 10,
    "HEATMAP_FIGSIZE": (24, 10),
    "HEATMAP_DPI": 150,
    "HEATMAP_GRID": (4, 3),        # rows x cols for 12-month layout

    "CAPACITY_HISTORY_DAYS": 30,    # Days of capacity history to display
    "FORECAST_DAYS_FORWARD": 60,    # Days to forecast capacity

    "EXTERNAL_TASK_LIMIT": 5,       # Max external tasks to show
    "UPCOMING_SHOOTS_LIMIT": 10,    # Max upcoming shoots to show
    "UPCOMING_DEADLINES_DAYS": 10,  # Days ahead for deadline list
}


# =============================================================================
# COMPUTED VALUES
# =============================================================================

def get_team_by_function(function_name):
    """Get all team members for a given function (Video, Design, Social, etc.)"""
    return {
        name: info for name, info in TEAM.items()
        if info["function"] == function_name
    }

def get_max_capacity(function_name=None):
    """Calculate total max capacity, optionally filtered by function"""
    members = TEAM.values() if not function_name else get_team_by_function(function_name).values()
    return sum(m["capacity"] for m in members)

def get_member_by_gid(gid):
    """Look up a team member by their Asana GID"""
    for name, info in TEAM.items():
        if info["gid"] == gid:
            return name, info
    return None, None

def get_project_gid(category, name):
    """Get a project GID by category and name"""
    return PROJECTS.get(category, {}).get(name)

def get_phase_multiplier(work_type, phase_name):
    """Get the phase multiplier for a work type and phase"""
    return SCORING["PHASE_MULTIPLIERS"].get(work_type, {}).get(phase_name, 1.0)


# Legacy computed values (backward compatibility)
MAX_CAPACITY = get_max_capacity("Video")  # Video team capacity
