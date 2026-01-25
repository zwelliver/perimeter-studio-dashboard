import requests
from requests.exceptions import HTTPError
import json
import re
import datetime
import os
import base64
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import replicate

# Load environment variables from .env file in the current directory
load_dotenv(".env")

# Asana setup
ASANA_PAT_BACKDROP = os.getenv("ASANA_PAT_BACKDROP")
PRODUCTION_PROJECT_ID = "1209597979075357"
ASANA_HEADERS = {"Authorization": f"Bearer {ASANA_PAT_BACKDROP}", "Content-Type": "application/json"}
TASK_LIST_ENDPOINT = f"https://app.asana.com/api/1.0/projects/{PRODUCTION_PROJECT_ID}/tasks?opt_fields=gid,name,created_at,modified_at,notes,custom_fields"
EVENTS_ENDPOINT = f"https://app.asana.com/api/1.0/projects/{PRODUCTION_PROJECT_ID}/events"

# Grok API setup (for text prompts only, switched from Claude to free up Claude API)
XAI_API_KEY = os.getenv("GROK_API_KEY")
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"
GROK_HEADERS = {
    "Authorization": f"Bearer {XAI_API_KEY}",
    "Content-Type": "application/json"
}
GROK_PROMPT = """Based on the provided Asana task details, generate 3 unique image prompts for virtual production backdrops. Ensure the prompts:
- Generate INDOOR environments by default (office, living room, kitchen, hallway, conference room, studio, library, etc.)
- Only generate outdoor environments if the task details specifically mention outdoor filming or locations
- Reflect the task's themes or context
- Are simple, grounded settings with no people
- Avoid specific objects or focal points, focusing on ambiance and space
Return JSON: {"prompts": ["prompt 1", "prompt 2", "prompt 3"]}."""

# Replicate API for FLUX.2 Pro (primary image generation)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN  # Set for replicate client

# Stable Diffusion setup (fallback if FLUX fails)
SD_API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY")
SD_ENDPOINT = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
SD_HEADERS = {"Authorization": f"Bearer {SD_API_KEY}", "Accept": "image/*"}

# Define last run and sync files with user-home-relative paths
LAST_RUN_FILE = os.path.expanduser("~/Scripts/StudioProcesses/production_last_run.txt")
SYNC_TOKEN_FILE = os.path.expanduser("~/Scripts/StudioProcesses/production_sync_token.txt")
PROCESSED_FILE = os.path.expanduser("~/Scripts/StudioProcesses/processed_backdrops.txt")

# Placeholder image (base64 for fallback)
PLACEHOLDER_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYSURBVChTYxg4wND/HzjAwP8fOACgKQAWTwq8xCo6SwAAAABJRU5ErkJggg=="

# Fallback backdrops (for names/complexity only)
FALLBACK_BACKDROPS = [
    {"name": "Backdrop 1", "complexity": "2/4"},
    {"name": "Backdrop 2", "complexity": "1/4"},
    {"name": "Backdrop 3", "complexity": "3/4"}
]

# Load processed tasks
def load_processed_tasks():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# Save processed task
def save_processed_task(gid):
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{gid}\n")

def get_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            last_run_str = f.read().strip()
        try:
            return datetime.datetime.fromisoformat(last_run_str)
        except ValueError:
            print(f"Invalid timestamp in {LAST_RUN_FILE}, resetting to default")
    return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

def update_last_run_time():
    current_time = datetime.datetime.now(datetime.timezone.utc)
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(current_time.isoformat())
    print(f"Updated last run time: {current_time}")

def get_sync_token():
    if os.path.exists(SYNC_TOKEN_FILE):
        with open(SYNC_TOKEN_FILE, 'r') as f:
            return f.read().strip()
    return None

def update_sync_token(new_token):
    if new_token:
        with open(SYNC_TOKEN_FILE, 'w') as f:
            f.write(new_token)
        print(f"Updated sync token: {new_token}")

def fetch_added_gids(sync_token):
    added_gids = set()
    params = {"sync": sync_token} if sync_token else {}
    try:
        response = requests.get(EVENTS_ENDPOINT, headers=ASANA_HEADERS, params=params)
        if response.status_code == 412:
            print("412 error, retrying without sync token after delay")
            time.sleep(2)
            response = requests.get(EVENTS_ENDPOINT, headers=ASANA_HEADERS)
            if response.status_code == 412:
                print("Retry failed with 412")
                response_data = response.json()
                new_sync_token = response_data.get("sync")
                update_sync_token(new_sync_token)
                return set()
        response.raise_for_status()
        data = response.json()
        events = data.get("data", [])
        added_gids = {event["resource"]["gid"] for event in events if event.get("action") == "added" and event.get("resource", {}).get("resource_type") == "task"}
        new_sync_token = data.get("sync")
        update_sync_token(new_sync_token)
        print(f"Tasks added: {len(added_gids)}")
    except Exception as e:
        print(f"Events Error: {e}")
    return added_gids

def fetch_task_gids():
    try:
        response = requests.get(TASK_LIST_ENDPOINT, headers=ASANA_HEADERS)
        response.raise_for_status()
        return [task["gid"] for task in response.json()["data"]]
    except Exception as e:
        print(f"Asana Error (task list): {e}")
        return []

def fetch_task_details(gid):
    endpoint = f"https://app.asana.com/api/1.0/tasks/{gid}?opt_fields=gid,name,created_at,modified_at,notes,custom_fields"
    try:
        response = requests.get(endpoint, headers=ASANA_HEADERS)
        response.raise_for_status()
        return response.json()["data"]
    except Exception as e:
        print(f"Asana Error (task {gid}): {e}")
        return None

def filter_new_tasks(tasks, added_gids, last_run_time, processed_tasks):
    new_tasks = []
    APPROVAL_FIELD = "Approval"
    VIRTUAL_LOCATION_FIELD = "Virtual Location"
    for task in tasks:
        gid = task["gid"]
        if gid in processed_tasks:
            print(f"Skipping processed task: {task['name']} (GID: {gid})")
            continue
        created_at = datetime.datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
        modified_at = datetime.datetime.fromisoformat(task['modified_at'].replace('Z', '+00:00'))
        custom_fields = {}
        for cf in task.get("custom_fields", []):
            if not isinstance(cf, dict):
                continue
            name = cf.get("name")
            if not name:
                continue
            if "enum_value" in cf and cf["enum_value"] is not None:
                value = cf["enum_value"].get("name")
            else:
                value = cf.get("text_value")
            custom_fields[name] = value
        is_approved = custom_fields.get(APPROVAL_FIELD) == "Approved"
        virtual_location_value = custom_fields.get(VIRTUAL_LOCATION_FIELD) or ""
        has_virtual_location = bool(virtual_location_value.strip() if isinstance(virtual_location_value, str) else False)
        is_newly_added = gid in added_gids
        if (is_newly_added or modified_at > last_run_time or created_at > last_run_time) and is_approved and not has_virtual_location:
            new_tasks.append(task)
            print(f" -> Added as new task for backdrop generation")
        else:
            print(f" -> Skipped")
    return new_tasks

def generate_prompts(project_details):
    payload = {
        "model": "grok-fast-turbo",  # Grok 4 fast for creative image prompt generation
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": "You are an AI assistant that generates image prompts for virtual production backdrops."},
            {"role": "user", "content": f"{GROK_PROMPT}\n\nTask details:\n{project_details}"}
        ]
    }
    prompts = []
    for attempt in range(3):
        try:
            response = requests.post(GROK_ENDPOINT, json=payload, headers=GROK_HEADERS, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
            else:
                json_content = content
            result = json.loads(json_content)
            prompts = result.get("prompts", [])
            if len(prompts) == 3:
                break
        except Exception as e:
            print(f"Grok prompt error (attempt {attempt+1}): {e}")
            time.sleep(2)
    if len(prompts) != 3:
        print("Using fallback prompts after Grok failed")
        prompts = [
            "Warm office space, soft lighting, photorealistic, no people",
            "Cozy living room, warm tones, photorealistic, no people",
            "Rustic kitchen, natural light, photorealistic, no people"
        ]
    return prompts

def generate_image(prompt):
    """Generate image using FLUX.2 Pro (primary) with Stable Diffusion fallback"""

    # Try FLUX.2 Pro first (best quality for Marble 3D generation)
    try:
        print(f"Generating with FLUX.2 Pro...")
        output = replicate.run(
            "black-forest-labs/flux-2-max",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",  # Wide format for virtual production
                "output_format": "png",
                "output_quality": 100,
                "safety_tolerance": 2,  # Allow professional production content
            }
        )

        # FLUX returns a FileOutput object, get the URL
        if output:
            image_url = str(output)  # Convert FileOutput to URL string
            # Download the image
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            image_content = img_response.content
            print(f"✅ FLUX.2 Pro generated successfully")
            return base64.b64encode(image_content).decode('utf-8')
    except Exception as e:
        print(f"⚠️  FLUX.2 Pro error: {e}, falling back to Stable Diffusion...")

    # Fallback to Stable Diffusion Ultra
    try:
        print(f"Generating with Stable Diffusion Ultra (fallback)...")
        files = {
            "prompt": (None, prompt),
            "aspect_ratio": (None, "21:9"),
            "output_format": (None, "png")
        }
        response = requests.post(SD_ENDPOINT, headers=SD_HEADERS, files=files, timeout=60)
        response.raise_for_status()
        image_content = response.content
        print(f"✅ Stable Diffusion generated successfully")
        return base64.b64encode(image_content).decode('utf-8')
    except Exception as e:
        print(f"❌ Stable Diffusion error: {e}")

    return None

def post_comment(task_id, comment):
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/stories"
    try:
        requests.post(url, headers=ASANA_HEADERS, json={"data": {"text": comment}})
        print(f"Commented on {task_id}")
    except Exception as e:
        print(f"Error commenting on {task_id}: {e}")

def attach_image(task_id, name, image_b64):
    try:
        image_content = base64.b64decode(image_b64 or PLACEHOLDER_IMAGE)
        url = f"https://app.asana.com/api/1.0/tasks/{task_id}/attachments"
        files = {"file": (f"{name}.png", image_content, "image/png")}
        response = requests.post(url, headers={"Authorization": f"Bearer {ASANA_PAT_BACKDROP}"}, files=files)
        response.raise_for_status()
        print(f"Attached {name}.png to {task_id}")
    except Exception as e:
        print(f"Error attaching image to {task_id}: {e}")

# Main execution
last_run_time = get_last_run_time()
sync_token = get_sync_token()
update_last_run_time()  # Update immediately

added_gids = fetch_added_gids(sync_token)
task_gids = fetch_task_gids()
tasks = [d for gid in task_gids if (d := fetch_task_details(gid)) is not None]
processed_tasks = load_processed_tasks()
new_tasks = filter_new_tasks(tasks, added_gids, last_run_time, processed_tasks)

print(f"Number of tasks to process: {len(new_tasks)}")

for task in new_tasks:
    task_name = task["name"]
    task_id = task["gid"]
    description = task.get("notes", "No description provided")
    project_details = f"{task_name}. {description}"
    print(f"Processing {task_name}")

    prompts = generate_prompts(project_details)
    print(f"Generated prompts: {prompts}")

    # Generate all 3 images in parallel for 3x performance boost
    print("Generating images in parallel...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all image generation tasks concurrently
        futures = [executor.submit(generate_image, prompt) for prompt in prompts]
        # Collect results as they complete
        images_b64 = [future.result() for future in futures]
    print(f"Generated {sum(1 for img in images_b64 if img)} images successfully")

    # Build backdrop list with generated images
    backdrops = []
    for i, (prompt, fallback, image_b64) in enumerate(zip(prompts, FALLBACK_BACKDROPS, images_b64)):
        description_clean = prompt.replace(", photorealistic, no people", "") if ", photorealistic, no people" in prompt else prompt
        backdrop = {
            "name": fallback["name"],
            "complexity": fallback["complexity"],
            "description": description_clean
        }
        if image_b64:
            backdrop["image"] = image_b64
        backdrops.append(backdrop)

    # If all images failed, still keep backdrops with descriptions (attach placeholders later)
    if all("image" not in b for b in backdrops):
        print(f"Image generation failed for {task_name}; using placeholders.")

    comment = "Stable Diffusion suggests:\n" + "\n".join(
        f"{i+1}. {b['name']} ({b['complexity']}) - {b.get('description', 'No description available')}"
        for i, b in enumerate(backdrops)
    ) + "\nImages attached (placeholders if generation failed)—pick one for ‘Virtual Location’!"
    post_comment(task_id, comment)

    for backdrop in backdrops:
        attach_image(task_id, backdrop["name"], backdrop.get("image"))

    save_processed_task(task_id)

# Final update
update_last_run_time()
