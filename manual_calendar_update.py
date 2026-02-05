#!/usr/bin/env python3
"""
Manual script to update the Unlimited Grace - January calendar event to Wednesday 1pm
"""

import os
import pickle
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Google Calendar config
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.pickle'

def get_calendar_service():
    """Authenticate and return Google Calendar service"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Need to re-authenticate. Run the main sync script first.")
            return None

    return build('calendar', 'v3', credentials=creds)

def find_and_update_event():
    """Find the Unlimited Grace event and update it to Wednesday 1pm"""
    service = get_calendar_service()
    if not service:
        return

    # Search for the event
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        q='Unlimited Grace',
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    target_event = None
    for event in events:
        if 'Unlimited Grace' in event.get('summary', '') and 'January' in event.get('summary', ''):
            target_event = event
            break

    if not target_event:
        print("❌ Could not find 'Unlimited Grace - January' event")
        return

    print(f"📅 Found event: {target_event['summary']}")
    print(f"🕐 Current time: {target_event['start']['dateTime']}")

    # Calculate Wednesday 1pm (Jan 29, 2026)
    wednesday_date = "2026-01-29"

    # Set to 1pm EST (18:00 UTC)
    new_start = f"{wednesday_date}T18:00:00.000Z"  # 1pm EST = 6pm UTC
    new_end = f"{wednesday_date}T19:00:00.000Z"    # 1 hour duration

    # Update the event
    target_event['start']['dateTime'] = new_start
    target_event['end']['dateTime'] = new_end

    updated_event = service.events().update(
        calendarId=CALENDAR_ID,
        eventId=target_event['id'],
        body=target_event
    ).execute()

    print(f"✅ Updated event to: {updated_event['start']['dateTime']}")
    print("🕐 Event is now set for 1:00 PM EST")

if __name__ == "__main__":
    print("🔄 Manually updating Unlimited Grace - January event...")
    find_and_update_event()