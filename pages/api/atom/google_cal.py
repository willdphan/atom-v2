import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, time, timedelta
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from pydub import AudioSegment
from elevenlabslib import ElevenLabsUser
import config as config
from dateutil.parser import parse
import pytz
import simpleaudio as sa
import io

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = '...'
CALENDAR_ID = '...'

api_key = config.ELEVEN_LABS_API_KEY
user = ElevenLabsUser(api_key)


def create_event(start_time, end_time, summary, attendees=None):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    event = {
        'summary': summary,
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
    print(
        f"Creating event with start time: {start_time} and end time: {end_time}")
    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {e}")
        traceback.print_exc()


def delete_event(event_id):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        print(f"Event deleted: {event_id}")
    except Exception as e:
        print(f"Error deleting event: {e}")
        traceback.print_exc()


def find_event(start_time):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
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


def parse_calendar_event_details(user_message):
    start_time, end_time = None, None
    try:
        start_time = parse(user_message, fuzzy=True)
        start_time = pytz.timezone('America/New_York').localize(start_time)
        end_time = start_time + timedelta(hours=1)
    except ValueError as e:
        print(f"Error parsing the date and time: {e}")

    return start_time, end_time


def play_ask_event_title():
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(
        "Sure thing! What would the event title be?")

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("intro.wav", format="wav")

    wave_obj = sa.WaveObject.from_wave_file("intro.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()


def get_events():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    timezone = pytz.timezone('America/New_York')
    now = datetime.now(timezone)
    start_of_day = timezone.localize(datetime.combine(now.date(), time.min))
    end_of_day = timezone.localize(datetime.combine(now.date(), time.max))
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=start_of_day.isoformat(), timeMax=end_of_day.isoformat(),
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return []

    output = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_time = datetime.fromisoformat(start).astimezone(timezone)
        end_time = datetime.fromisoformat(end).astimezone(timezone)
        output.append({
            'start_time': start_time,
            'end_time': end_time,
            'summary': event['summary'],
        })

    return output
