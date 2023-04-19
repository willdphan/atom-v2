import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import config 

SCOPES = "..."
SERVICE_ACCOUNT_FILE = "..."
CALENDAR_ID = "..."

def create_event(start_time, end_time, summary, attendees=None, event_title=None):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': event_title if event_title else summary,
        'description': summary,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'attendees': [{'email': email.strip()} for email in attendees.split(',')] if attendees else [],
    }

    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
        return event.get('htmlLink')  # Add this line to return the event link
    except Exception as e:
        print(f"Error creating event: {e}")
        traceback.print_exc()
        return None  # Return None in case of an error


def delete_event(event_id):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        print(f"Event deleted: {event_id}")
    except Exception as e:
        print(f"Error deleting event: {e}")
        traceback.print_exc()

def find_event(start_time):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    try:
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=start_time.isoformat(), maxResults=1,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No events found.')
            return None
        else:
            return events[0]
    except Exception as e:
        print(f"Error finding event: {e}")
        traceback.print_exc()
        return None

def list_upcoming_events_today():
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now, maxResults=10,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    return events