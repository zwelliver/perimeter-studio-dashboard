#!/usr/bin/env python3
"""
Create a 'Film Date' custom field in Asana projects for calendar integration
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv(".env")

ASANA_PAT = os.getenv('ASANA_PAT_SCORER')
ASANA_HEADERS = {
    'Authorization': f'Bearer {ASANA_PAT}',
    'Content-Type': 'application/json'
}

# Your workspace GID (get from any project)
WORKSPACE_GID = '12090996748128'  # perimeter.org workspace

ASANA_PROJECTS = {
    'Preproduction': '1208336083003480',
    'Production': '1209597979075357',
    'Post Production': '1209581743268502',
    'Forecast': '1212059678473189'
}

def create_custom_field():
    """Create the Film Date custom field in the workspace"""
    print("Creating 'Film Date' custom field...")

    # Create custom field
    response = requests.post(
        f'https://app.asana.com/api/1.0/workspaces/{WORKSPACE_GID}/custom_fields',
        headers=ASANA_HEADERS,
        json={
            'data': {
                'name': 'Film Date',
                'description': 'The scheduled date for filming/production (syncs to Google Calendar)',
                'resource_subtype': 'date',
                'type': 'date'
            }
        }
    )

    if response.status_code == 201:
        field_data = response.json()['data']
        field_gid = field_data['gid']
        print(f"✅ Created 'Film Date' custom field: {field_gid}")
        return field_gid
    else:
        print(f"⚠️ Error creating field: {response.status_code}")
        print(response.json())
        return None

def add_field_to_projects(field_gid):
    """Add the custom field to all projects"""
    print(f"\nAdding 'Film Date' field to projects...")

    for project_name, project_gid in ASANA_PROJECTS.items():
        print(f"  Adding to {project_name}...", end=' ')

        response = requests.post(
            f'https://app.asana.com/api/1.0/projects/{project_gid}/addCustomFieldSetting',
            headers=ASANA_HEADERS,
            json={
                'data': {
                    'custom_field': field_gid,
                    'is_important': True  # Show in task list
                }
            }
        )

        if response.status_code == 200:
            print("✅")
        else:
            print(f"⚠️ Error: {response.status_code}")

if __name__ == '__main__':
    print("🎬 Creating 'Film Date' Custom Field for Calendar Integration\n")
    print("=" * 70)

    # Create the field
    field_gid = create_custom_field()

    if field_gid:
        # Add to all projects
        add_field_to_projects(field_gid)

        print("\n" + "=" * 70)
        print("✅ COMPLETE!")
        print(f"\nFilm Date Field GID: {field_gid}")
        print("\nNext steps:")
        print("1. Add this GID to your .env file as FILM_DATE_FIELD_GID")
        print("2. Set up Google Calendar API credentials")
        print("3. Run the calendar sync script")
    else:
        print("\n⚠️ Field creation failed. Check if field already exists.")
