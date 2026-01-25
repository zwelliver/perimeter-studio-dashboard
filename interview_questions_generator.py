#!/usr/bin/env python3
"""
Interview Questions Generator for Testimony/Story Videos
=========================================================
Automatically generates tailored interview questions for testimony and story-type
videos based on Asana task information. Triggered after video_scorer.py processes
a qualifying task.

Qualifying criteria:
- Type = "Enriching" AND contains testimony/story keywords
- OR task name contains: testimony, story, WOV, generosity, retreat highlight

Output: Adds suggested interview questions as a comment on the Asana task.
"""

import os
import re
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "interview_questions.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
ASANA_HEADERS = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}

# Grok API - Primary AI for question generation (switched from Claude to free up Claude API)
XAI_API_KEY = os.getenv("GROK_API_KEY")
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {
    "Authorization": f"Bearer {XAI_API_KEY}",
    "Content-Type": "application/json"
}
GROK_MODEL = "grok-4-fast-non-reasoning"  # Grok 4 fast for creative interview questions

# Tracking file for processed tasks
PROCESSED_FILE = os.path.join(BASE_DIR, "interview_questions_processed.txt")

# Keywords that identify testimony/story videos (interview-based)
TESTIMONY_KEYWORDS = [
    'testimony', 'testimonial', 'story', 'stories',
    'generosity', 'stewardship',
    'retreat highlight', 'highlight video',
    'member story', 'faith story', 'journey',
    'how god', 'transformation', 'life change'
]

# Keywords that EXCLUDE a task (scripted content, not interviews)
EXCLUDE_KEYWORDS = [
    'wov', 'weekly opportunity', 'scripted',
    'announcement', 'promo only', 'graphics'
]

SYSTEM_PROMPT = """You are an expert video producer and interviewer for Perimeter Church,
a large evangelical church in Atlanta. Your job is to create thoughtful, authentic interview
questions that help people share their faith stories naturally.

CRITICAL RULE FOR VIDEO EDITING:
Questions MUST be phrased so the guest REPEATS THE CONTEXT in their answer. This allows
editors to use the answer as a standalone clip without needing the question.

EXAMPLES OF GOOD vs BAD PHRASING:

❌ BAD: "How long have you been at Perimeter?"
✅ GOOD: "Tell me about when you first came to Perimeter and how long you've been here."
(Guest will say: "I first came to Perimeter about 5 years ago when...")

❌ BAD: "What happened at the retreat?"
✅ GOOD: "Take me back to that moment at the Women's Retreat—describe what was happening and what God showed you."
(Guest will say: "At the Women's Retreat, I was sitting in the session when...")

❌ BAD: "How did that change things?"
✅ GOOD: "Describe how that experience changed your marriage/faith/perspective."
(Guest will say: "That experience completely changed my marriage because...")

❌ BAD: "What would you tell someone else?"
✅ GOOD: "If you could sit down with another woman going through something similar, what would you want her to know?"
(Guest will say: "If I could sit down with another woman going through this, I'd tell her...")

Guidelines for interview questions:
1. Start with easy, comfortable questions to help the person relax
2. Progress to deeper, more reflective questions
3. ALWAYS phrase questions so answers can stand alone (guest restates context)
4. Use "Tell me about...", "Describe...", "Take me back to...", "Walk me through..."
5. Include specific details from the video brief (ministry, event, topic, audience)
6. End with forward-looking or encouraging questions
7. Keep questions open-ended (avoid yes/no questions)
8. Use conversational language, not formal or churchy jargon
9. Include follow-up prompts that also encourage context restatement

The questions should feel like a warm conversation, not an interrogation.
Perimeter's values: authentic faith, gospel-centered, community-focused, missional living.

Return your response in this exact JSON format:
{
    "opening_questions": ["question 1", "question 2"],
    "core_questions": ["question 1", "question 2", "question 3", "question 4"],
    "deeper_questions": ["question 1", "question 2"],
    "closing_questions": ["question 1"],
    "follow_up_prompts": ["prompt 1", "prompt 2"],
    "interviewer_notes": "Brief notes for the interviewer about approach/tone"
}
"""


def load_processed_tasks():
    """Load set of task GIDs that have already received interview questions."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_processed_task(gid):
    """Mark a task as having received interview questions."""
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{gid}\n")


def is_testimony_video(task_name, task_notes, task_type):
    """
    Determine if a task qualifies for interview question generation.

    Criteria:
    - Type is "Enriching" AND contains testimony/story keywords
    - OR task name/notes strongly indicate testimony content
    - EXCLUDE WOV and other scripted content

    Note: WOV (Weekly Opportunity Video) is scripted, not interview-based,
    so it should NOT receive interview questions.
    """
    task_name_lower = task_name.lower()
    task_notes_lower = (task_notes or "").lower()
    combined_text = f"{task_name_lower} {task_notes_lower}"

    # FIRST: Check for exclusions (WOV, scripted content, etc.)
    is_excluded = any(excl in combined_text for excl in EXCLUDE_KEYWORDS)
    if is_excluded:
        logger.debug(f"Task excluded (scripted/WOV content): {task_name}")
        return False

    # Check for testimony keywords
    has_testimony_keyword = any(kw in combined_text for kw in TESTIMONY_KEYWORDS)

    # Type check
    is_enriching = task_type and task_type.lower() == "enriching"

    # Strong indicators in task name (these alone qualify, but NOT WOV)
    strong_indicators = ['testimony', 'testimonial', 'story video', 'interview']
    has_strong_indicator = any(ind in task_name_lower for ind in strong_indicators)

    # Qualify if: (Enriching + keyword) OR strong indicator
    qualifies = (is_enriching and has_testimony_keyword) or has_strong_indicator

    if qualifies:
        logger.info(f"Task qualifies for interview questions: {task_name}")

    return qualifies


def extract_context_from_task(task_data):
    """
    Extract ALL relevant context from task data for question generation.
    Pulls from custom fields (form submissions) and task notes.
    """
    context = {
        "task_name": task_data.get("name", ""),
        "description": task_data.get("notes", ""),
        "person_name": None,
        # Form fields
        "video_type": None,        # Equipping, Enriching, Ministry Support, Partner Support
        "audience": None,          # Church-wide, Community, People Groups, Ministry Groups
        "scope": None,             # Evergreen, Seasonal, Event-driven, Short-term
        "duration": None,          # Video duration
        "category": None,          # Ministry category
        "ministry": None,          # Related ministry/department
        "topic": None,             # Inferred topic
        "occasion": None,          # Seasonal occasion
        "start_date": task_data.get("start_on"),
        "due_date": task_data.get("due_on"),
    }

    task_name = context["task_name"]
    notes = context["description"]

    # Extract custom fields from form submission
    custom_fields = task_data.get("custom_fields", [])
    for cf in custom_fields:
        cf_name = cf.get("name", "").lower()

        # Get enum value if present
        enum_val = cf.get("enum_value", {})
        enum_name = enum_val.get("name") if enum_val else None

        # Get text/number value
        text_val = cf.get("text_value")
        num_val = cf.get("number_value")

        # Map custom fields
        if "type" in cf_name and enum_name:
            context["video_type"] = enum_name
        elif "audience" in cf_name and enum_name:
            context["audience"] = enum_name
        elif "scope" in cf_name or "longevity" in cf_name:
            context["scope"] = enum_name
        elif "duration" in cf_name:
            context["duration"] = enum_name or text_val
        elif "category" in cf_name and enum_name:
            context["category"] = enum_name
        elif "ministry" in cf_name or "department" in cf_name:
            context["ministry"] = enum_name or text_val

    # Try to extract person's name from task name
    name_patterns = [
        r'[-–:]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?:\s+[Tt]estimony|\s+[Ss]tory)?$',  # "Something - John Smith" or "Something - John Smith Testimony"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+[Tt]estimony',  # "John Smith Testimony"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+[Ss]tory',  # "John Smith Story"
        r'[Tt]estimony\s*[-–:]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',  # "Testimony - John Smith"
    ]

    for pattern in name_patterns:
        match = re.search(pattern, task_name)
        if match:
            name = match.group(1).strip()
            # Filter out common non-name words
            non_names = ['Women', 'Men', 'Student', 'Youth', 'Vision', 'Retreat', 'Generosity', 'Stewardship', 'Ministry', 'Church']
            if not any(name.startswith(nn) for nn in non_names):
                context["person_name"] = name
                break

    # Infer ministry from task name/notes if not in custom fields
    if not context["ministry"]:
        ministry_keywords = {
            "women": "Women's Ministry",
            "men's": "Men's Ministry",
            "student": "Student Ministry",
            "youth": "Student Ministry",
            "young adult": "Young Adults",
            "kids": "Children's Ministry",
            "children": "Children's Ministry",
            "marriage": "Marriage Ministry",
            "camp": "Camp All-American",
            "belong": "Belong Ministry",
            "generosity": "Stewardship/Generosity",
            "stewardship": "Stewardship/Generosity",
            "mission": "Missions",
            "global": "Global Outreach",
            "vision night": "Vision/Leadership"
        }
        combined = f"{task_name} {notes}".lower()
        for keyword, ministry in ministry_keywords.items():
            if keyword in combined:
                context["ministry"] = ministry
                break

    # Infer topic from task name/notes
    topic_keywords = {
        "generosity": "generosity and giving",
        "stewardship": "stewardship and faithful living",
        "retreat": "retreat experience",
        "transformation": "life transformation",
        "faith journey": "faith journey",
        "salvation": "coming to faith",
        "baptism": "baptism",
        "small group": "small group community",
        "serving": "serving",
        "marriage": "marriage",
        "parenting": "parenting",
        "healing": "healing and restoration",
        "grief": "grief and loss",
        "addiction": "freedom and recovery",
        "testimony": "faith story"
    }
    combined = f"{task_name} {notes}".lower()
    for keyword, topic in topic_keywords.items():
        if keyword in combined:
            context["topic"] = topic
            break

    # Check for seasonal/occasion context
    occasion_keywords = {
        "easter": "Easter",
        "christmas": "Christmas",
        "advent": "Advent",
        "holy week": "Holy Week",
        "thanksgiving": "Thanksgiving",
        "vision night": "Vision Night"
    }
    for keyword, occasion in occasion_keywords.items():
        if keyword in combined:
            context["occasion"] = occasion
            break

    return context


def build_user_prompt(context):
    """Build the user prompt with ALL available form context."""
    # Build context section with all available info
    context_lines = []

    if context.get('person_name'):
        context_lines.append(f"- **Person being interviewed:** {context['person_name']}")

    if context.get('description'):
        context_lines.append(f"- **Project description/notes:** {context['description']}")

    if context.get('video_type'):
        context_lines.append(f"- **Video type/purpose:** {context['video_type']}")

    if context.get('audience'):
        context_lines.append(f"- **Target audience:** {context['audience']}")

    if context.get('scope'):
        context_lines.append(f"- **Content scope:** {context['scope']}")

    if context.get('duration'):
        context_lines.append(f"- **Video duration:** {context['duration']}")

    if context.get('category'):
        context_lines.append(f"- **Category:** {context['category']}")

    if context.get('ministry'):
        context_lines.append(f"- **Ministry/Department:** {context['ministry']}")

    if context.get('topic'):
        context_lines.append(f"- **Topic focus:** {context['topic']}")

    if context.get('occasion'):
        context_lines.append(f"- **Occasion/Season:** {context['occasion']}")

    if context.get('due_date'):
        context_lines.append(f"- **Due date:** {context['due_date']}")

    context_section = "\n".join(context_lines) if context_lines else "- General testimony/faith story"

    return f"""Generate interview questions for this testimony/story video:

**Video Title:** {context['task_name']}

**VIDEO BRIEF DETAILS:**
{context_section}

IMPORTANT REMINDERS:
1. Phrase ALL questions so the guest will RESTATE THE CONTEXT in their answer (for editing)
2. Use the specific details above (ministry, topic, occasion, audience) in your questions
3. If this is for a specific ministry (Women's, Men's, Students, etc.), tailor questions to that context
4. If there's a specific topic (generosity, retreat, marriage), include questions specific to that experience
5. If there's a target audience, consider what would resonate with them

Generate thoughtful, personalized interview questions that will help this person share their story
in a way that can be edited into standalone clips."""


def generate_questions_claude(context):
    """Generate interview questions using Grok API."""
    if not XAI_API_KEY:
        logger.warning("No Grok API key found")
        return None

    user_prompt = build_user_prompt(context)

    payload = {
        "model": GROK_MODEL,
        "max_tokens": 1500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(GROK_ENDPOINT, json=payload, headers=GROK_HEADERS, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        else:
            logger.error("Could not parse JSON from Grok response")
            return None

    except Exception as e:
        logger.error(f"Grok API error: {e}")
        return None


def generate_questions(context):
    """
    Generate interview questions using Claude API.
    (Migrated from Grok - xAI API deprecated Feb 20, 2026)
    """
    return generate_questions_claude(context)


def format_questions_for_comment(questions_data, context):
    """Format the generated questions as a nicely formatted Asana comment."""
    if not questions_data:
        return None

    person_name = context.get('person_name', 'the guest')

    lines = [
        "🎬 **SUGGESTED INTERVIEW QUESTIONS**",
        f"Generated for: {context['task_name']}",
        "",
        "---",
        "",
        "**OPENING (Help them relax)**"
    ]

    for q in questions_data.get("opening_questions", []):
        lines.append(f"• {q}")

    lines.extend(["", "**CORE STORY QUESTIONS**"])
    for q in questions_data.get("core_questions", []):
        lines.append(f"• {q}")

    lines.extend(["", "**DEEPER REFLECTION**"])
    for q in questions_data.get("deeper_questions", []):
        lines.append(f"• {q}")

    lines.extend(["", "**CLOSING**"])
    for q in questions_data.get("closing_questions", []):
        lines.append(f"• {q}")

    if questions_data.get("follow_up_prompts"):
        lines.extend(["", "**FOLLOW-UP PROMPTS** (use to go deeper)"])
        for p in questions_data.get("follow_up_prompts", []):
            lines.append(f"• \"{p}\"")

    if questions_data.get("interviewer_notes"):
        lines.extend(["", f"**Notes for interviewer:** {questions_data['interviewer_notes']}"])

    lines.extend([
        "",
        "---",
        f"_Auto-generated by Studio AI on {datetime.now().strftime('%b %d, %Y at %I:%M %p')}_"
    ])

    return "\n".join(lines)


def add_comment_to_task(task_gid, comment_text):
    """Add a comment to an Asana task."""
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}/stories"
    payload = {
        "data": {
            "text": comment_text
        }
    }

    try:
        response = requests.post(url, json=payload, headers=ASANA_HEADERS)
        response.raise_for_status()
        logger.info(f"Successfully added interview questions comment to task {task_gid}")
        return True
    except Exception as e:
        logger.error(f"Failed to add comment to task {task_gid}: {e}")
        return False


def process_task(task_gid):
    """
    Main function to process a single task.
    Fetches task details, checks if it qualifies, generates questions, and adds comment.
    """
    # Fetch task details
    url = f"https://app.asana.com/api/1.0/tasks/{task_gid}?opt_fields=name,notes,custom_fields"

    try:
        response = requests.get(url, headers=ASANA_HEADERS)
        response.raise_for_status()
        task_data = response.json()["data"]
    except Exception as e:
        logger.error(f"Failed to fetch task {task_gid}: {e}")
        return False

    task_name = task_data.get("name", "")
    task_notes = task_data.get("notes", "")

    # Extract Type from custom fields
    task_type = None
    for cf in task_data.get("custom_fields", []):
        if cf.get("name") == "Type" and cf.get("enum_value"):
            task_type = cf["enum_value"].get("name")
            break

    # Check if task qualifies
    if not is_testimony_video(task_name, task_notes, task_type):
        logger.info(f"Task {task_name} does not qualify for interview questions")
        return False

    # Extract context
    context = extract_context_from_task(task_data)

    # Generate questions (Grok first since it's proven to work, Claude as fallback)
    questions = generate_questions(context)

    if not questions:
        logger.error(f"Failed to generate questions for task {task_name}")
        return False

    # Format and add comment
    comment = format_questions_for_comment(questions, context)
    if comment and add_comment_to_task(task_gid, comment):
        save_processed_task(task_gid)
        return True

    return False


def process_recent_tasks():
    """
    Scan recent tasks and process any that qualify for interview questions.
    This can be run standalone or called from video_scorer.py after scoring.
    """
    from video_scorer import PROJECT_GIDS, ASANA_HEADERS

    processed = load_processed_tasks()
    tasks_processed = 0

    for project_name, project_gid in PROJECT_GIDS.items():
        # Only check Production and Post Production (where testimonies usually are)
        if project_name not in ["Production", "Post Production", "Preproduction"]:
            continue

        url = f"https://app.asana.com/api/1.0/projects/{project_gid}/tasks?opt_fields=gid,name,notes,custom_fields,created_at"

        try:
            response = requests.get(url, headers=ASANA_HEADERS)
            response.raise_for_status()
            tasks = response.json()["data"]
        except Exception as e:
            logger.error(f"Failed to fetch tasks from {project_name}: {e}")
            continue

        for task in tasks:
            gid = task["gid"]

            # Skip if already processed
            if gid in processed:
                continue

            # Process the task
            if process_task(gid):
                tasks_processed += 1

    logger.info(f"Processed {tasks_processed} tasks for interview questions")
    return tasks_processed


# Entry point for integration with video_scorer.py
def generate_interview_questions_for_task(task_gid, task_name, task_notes, task_type):
    """
    Called by video_scorer.py after scoring a task.
    Returns True if questions were generated and added.
    """
    processed = load_processed_tasks()

    if task_gid in processed:
        logger.debug(f"Task {task_gid} already has interview questions")
        return False

    if not is_testimony_video(task_name, task_notes, task_type):
        return False

    return process_task(task_gid)


if __name__ == "__main__":
    # When run directly, scan all projects for qualifying tasks
    logger.info("Starting interview questions generator scan...")
    process_recent_tasks()
    logger.info("Interview questions generator complete.")
