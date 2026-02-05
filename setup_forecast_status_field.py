#!/usr/bin/env python3
"""
One-time setup script to create the "Forecast Status" custom field in Asana
and add it to the Forecast project.

Run this once on your server before using the forecast_status_automation.py

Usage: python setup_forecast_status_field.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ASANA_PAT = os.getenv("ASANA_PAT_SCORER")
FORECAST_PROJECT_GID = '1212059678473189'

headers = {
    "Authorization": f"Bearer {ASANA_PAT}",
    "Content-Type": "application/json"
}


def main():
    print("=" * 60)
    print("Setting up 'Forecast Status' Custom Field")
    print("=" * 60)
    print()

    if not ASANA_PAT:
        print("❌ Error: ASANA_PAT_SCORER not found in environment")
        return

    # First, check if the field already exists
    print("Checking for existing 'Forecast Status' field...")
    project_url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}"
    project_response = requests.get(
        project_url,
        headers=headers,
        params={"opt_fields": "workspace.gid,custom_field_settings.custom_field.name"}
    )
    project_response.raise_for_status()
    project_data = project_response.json()['data']

    workspace_gid = project_data['workspace']['gid']
    print(f"   Workspace GID: {workspace_gid}")

    # Check existing fields
    existing_fields = project_data.get('custom_field_settings', [])
    for setting in existing_fields:
        field = setting.get('custom_field', {})
        if field.get('name') == 'Forecast Status':
            print(f"✅ 'Forecast Status' field already exists! (GID: {field.get('gid')})")
            print("   No action needed.")
            return

    print("   Field not found - creating it now...")
    print()

    # Create the custom field
    print("Creating 'Forecast Status' custom field...")
    custom_field_url = "https://app.asana.com/api/1.0/custom_fields"
    payload = {
        "data": {
            "workspace": workspace_gid,
            "name": "Forecast Status",
            "resource_subtype": "enum",
            "enum_options": [
                {"name": "Pipeline", "color": "blue"},
                {"name": "Ready for Preproduction", "color": "green"},
                {"name": "On Hold", "color": "yellow"},
                {"name": "Cancelled", "color": "red"}
            ],
            "description": "Status of forecasted projects. Set to 'Ready for Preproduction' to automatically move to the Preproduction project."
        }
    }

    response = requests.post(custom_field_url, headers=headers, json=payload)

    if response.status_code == 201:
        custom_field = response.json()['data']
        print(f"✅ Created custom field: {custom_field['name']}")
        print(f"   GID: {custom_field['gid']}")
        print()

        # Add the custom field to the Forecast project
        print("Adding field to Forecast project...")
        add_field_url = f"https://app.asana.com/api/1.0/projects/{FORECAST_PROJECT_GID}/addCustomFieldSetting"
        add_payload = {
            "data": {
                "custom_field": custom_field['gid'],
                "is_important": True
            }
        }

        add_response = requests.post(add_field_url, headers=headers, json=add_payload)
        if add_response.status_code == 200:
            print("✅ Added 'Forecast Status' field to Forecast project")
        else:
            print(f"❌ Error adding to project: {add_response.text}")
            return
    else:
        print(f"❌ Error creating field: {response.status_code}")
        print(f"   Response: {response.text}")
        return

    print()
    print("=" * 60)
    print("✅ Setup complete!")
    print()
    print("The 'Forecast Status' field is now available in your Forecast project.")
    print()
    print("Field options:")
    print("   • Pipeline (blue) - Task is in planning phase")
    print("   • Ready for Preproduction (green) - Will be auto-moved")
    print("   • On Hold (yellow) - Task is paused")
    print("   • Cancelled (red) - Task is cancelled")
    print()
    print("Next: Set up cron jobs by running 'crontab -e' and adding")
    print("the entries from cron_setup.txt")
    print("=" * 60)


if __name__ == '__main__':
    main()
