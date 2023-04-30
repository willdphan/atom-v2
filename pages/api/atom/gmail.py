import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def list_unread_emails():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    return results.get('messages', [])

def announce_unread_emails():
    unread_emails = list_unread_emails()
    count = len(unread_emails)
    return f"You have {count} unread emails."

def create_draft_email(subject, body, to):
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    message = {
        'subject': subject,
        'body': body,
        'to': to
    }
    create_message = {'message': {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}}
    draft = service.users().drafts().create(userId='me', body=create_message).execute()
    return draft
