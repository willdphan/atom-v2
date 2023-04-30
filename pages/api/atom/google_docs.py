from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config
from elevenlabslib import ElevenLabsUser
from pydub import AudioSegment
import simpleaudio as sa
import io

api_key = config.ELEVEN_LABS_API_KEY
user = ElevenLabsUser(api_key)

def create_google_doc(title, initial_text):
    try:
        SCOPES = ['https://www.googleapis.com/auth/documents',
                  'https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = '...'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        service = build('docs', 'v1', credentials=credentials)
        body = {
            'title': title
        }
        doc = service.documents().create(body=body).execute()
        document_id = doc.get("documentId")
        print(F'Created document with title: {doc.get("title")} and URL:'
              F'https://docs.google.com/document/d/{document_id}')

        # Set up the Drive API client
        drive_service = build('drive', 'v3', credentials=credentials)

        document_id = doc.get("documentId")

        # Add the initial text to the Google Doc
        edit_google_doc(document_id, initial_text)

        # Give the user edit access to the document
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': config.GOOGLE_DOCS_ID
        }
        drive_service.permissions().create(
            fileId=document_id, body=permission, fields='id').execute()

        return document_id

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

def edit_google_doc(document_id, text):
    try:
        SCOPES = ['https://www.googleapis.com/auth/documents',
                  'https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'pages/api/google_docs_credentials.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        service = build('docs', 'v1', credentials=credentials)

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': text
                }
            }
        ]

        result = service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()

        return result

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

def play_ask_doc_title():
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(
        "Okay, what would the draft title be?")

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("intro.wav", format="wav")

    wave_obj = sa.WaveObject.from_wave_file("intro.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()