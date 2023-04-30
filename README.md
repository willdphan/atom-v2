# Atom, a Personalized Chat Assistant

ATOM is a personal assistant for managing and reviewing my schedule.

It uses various APIs and packages such as OpenAI, ElevenLabs, Google Calendar, and Twilio to offer several features such as creating/deleting calendar events and searching the internet for answers to specific questions. 

The code uses a microphone to receive audio inputs from users, transcribes them into text, and then generates audio responses for the user.

## Some Requirements
    Python 3.x
    openai
    elevenlabslib
    pydub
    simpleaudio
    speech_recognition
    search
    twilio
    langchain
    google-api-python-client
    google_docs
    twilio_utils
    screen_capture

## Getting Started
Install the required dependencies:

    pip install -r requirements
    
Set the API keys and authentication tokens in `config.py` and `google_cal`.

Run the code by executing the command python `atom.py` in your terminal or IDE.

## Main Features
1. Create, delete, and view Google Calendar events using Google API.
2. Searching the internet for answers to specific questions using the Google API.
3. Text-to-speech synthesis and speech-to-text recognition using ElevenLabs API and speech_recognition package.
4. Sending SMS to recipients using Twilio API.
5. Using OpenAI API for natural language processing.
6. Microsoft Azure's Computer Vision
7. Create Drafts with Google Docs.

Disclaimer
Please note that the code provided here is only for educational purposes and may not work as expected when used in a production environment.

## License

This script is open-source and licensed under the MIT License. For more details, check the [LICENSE](LICENSE) file.