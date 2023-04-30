import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import streamlit as st
import atom.config as config

SERVICE_ACCOUNT_FILE="..."
SCOPES="..."
CALENDAR_ID="..."

st.set_page_config(page_title="Google Calendar API", page_icon=":date:")

@st.cache(persist=True)
def get_service():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_event(start_time, end_time, summary, attendees=None):
    service = get_service()
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
    st.write(f"Creating event with start time: {start_time} and end time: {end_time}")
    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        st.success(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        st.error(f"Error creating event: {e}")
        st.error(traceback.format_exc())

def delete_event(event_id):
    service = get_service()
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        st.success(f"Event deleted: {event_id}")
    except Exception as e:
        st.error(f"Error deleting event: {e}")
        st.error(traceback.format_exc())

def find_event(start_time):
    service = get_service()
    try:
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=start_time.isoformat(), maxResults=1,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            st.write('No events found.')
            return None
        else:
            return events[0]
    except Exception as e:
        st.error(f"Error finding event: {e}")
        st.error(traceback.format_exc())
        return None

def list_upcoming_events_today():
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    service = get_service()
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now, maxResults=10,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        st.write('No upcoming events found.')
    return events


# Create the Streamlit app
def main():
    st.title("Google Calendar API")
    menu = ["Home", "Create Event", "Delete Event", "Find Event", "List Events"]
    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Home":
        st.write("Welcome to the Google Calendar API app! Use the sidebar to navigate.")

    elif choice == "Create Event":
        st.subheader("Create a new event")
        start_time = st.date_input("Start date", value=datetime.today())
        start_time = datetime.combine(start_time, datetime.min.time())
        start_time = start_time + timedelta(hours=1)  # Default start time is 1 hour from now
        end_time = st.date_input("End date", value=datetime.today())
        end_time = datetime.combine(end_time, datetime.min.time())
        end_time = end_time + timedelta(hours=2)  # Default end time is 2 hours from now
        summary = st.text_input("Event summary")
        attendees = st.text_input("Attendees (comma-separated)")

        if st.button("Create event"):
            create_event(start_time, end_time, summary, attendees)

    elif choice == "Delete Event":
        st.subheader("Delete an event")
        event_id = st.text_input("Event ID")

        if st.button("Delete event"):
            delete_event(event_id)

    elif choice == "Find Event":
        st.subheader("Find an event")
        start_time = st.date_input("Start date", value=datetime.today())
        start_time = datetime.combine(start_time, datetime.min.time())

        if st.button("Find event"):
            event = find_event(start_time)
            if event:
                st.write(f"Event summary: {event['summary']}")
                st.write(f"Start time: {event['start'].get('dateTime')}")
                st.write(f"End time: {event['end'].get('dateTime')}")
                if event.get('attendees'):
                    st.write("Attendees:")
                    for attendee in event['attendees']:
                        st.write(f"- {attendee['email']}")

    elif choice == "List Events":
        st.subheader("Upcoming events today")
        events = list_upcoming_events_today()

        if events:
            for event in events:
                st.write(f"{event['summary']} - {event['start'].get('dateTime')}")

if __name__ == "__main__":
    main()

