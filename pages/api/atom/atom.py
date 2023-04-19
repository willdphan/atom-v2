from datetime import timedelta
import openai
from elevenlabslib import *
from pydub import AudioSegment
from pydub.playback import play
import io
import config
import time
import speech_recognition as sr
import simpleaudio as sa
from search import search_google
from twilio.rest import Client
import os
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain.agents import load_tools
from google_cal import create_event, delete_event, find_event, list_upcoming_events_today
import pytz
import re
from dateutil.parser import parse



os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY

twilio_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
openai.api_key = config.OPENAI_API_KEY
api_key = config.ELEVEN_LABS_API_KEY
from elevenlabslib import ElevenLabsUser
user = ElevenLabsUser(api_key)

# INTRO MESSAGE

# def play_intro_message():
#     voice = user.get_voices_by_name("Antoni")[0]
#     audio = voice.generate_audio_bytes("Hello, I am ATOM, your AI executive assistant. How can I help you today?")

#     audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
#     audio.export("intro.wav", format="wav")

#     wave_obj = sa.WaveObject.from_wave_file("intro.wav")
#     play_obj = wave_obj.play()
#     play_obj.wait_done()

# play_intro_message()

def play_ask_event_title():
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes("Please say the event title")

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("intro.wav", format="wav")

    wave_obj = sa.WaveObject.from_wave_file("intro.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

messages = ["You are an AI executive assistant named ATOM. Provide responses less than 15 words."]

def send_sms(sms_text, recipient_phone_number):
    print(f"Sending SMS to {recipient_phone_number} with content: {sms_text}")
    message = twilio_client.messages.create(
        body=sms_text,
        from_=config.TWILIO_PHONE_NUMBER,
        to=recipient_phone_number,
    )
    print(f"SMS sent to {recipient_phone_number}. Message SID: {message.sid}")

def parse_calendar_event_details(user_message):
    start_time, end_time = None, None
    try:
        start_time = parse(user_message, fuzzy=True)
        start_time = pytz.timezone('America/New_York').localize(start_time)
        end_time = start_time + timedelta(hours=1)
    except ValueError as e:
        print(f"Error parsing the date and time: {e}")

    return start_time, end_time


def transcribe(audio):
    global messages

    source_urls = []  # Initialize the variable at the beginning of the function

    audio_file = open(audio, "rb")
    print(f"Audio file size: {os.path.getsize(audio)} bytes")
    print("Transcribing audio...")
    transcript_response = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = transcript_response['text'].strip()
    user_message = transcript.strip()

    prompt = messages[-1]
    prompt += f"\nUser: {user_message}"

    # START LISTENING

    if "stop listening" in user_message.lower():
        return False  # Return False when the keyword is detected


    # CALENDAR
    
    user_message_lower = user_message.lower()

    if "create an event" in user_message_lower:
        start_time, end_time = parse_calendar_event_details(user_message)
        if start_time and end_time:
            # Prompt the user to say the event title
            system_message = "What would the event title be?"
            print(system_message)
            play_ask_event_title()
        
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        # Use speech recognition to convert the user's speech to text
        try:
            event_title = recognizer.recognize_google(audio)
            create_event(start_time, end_time, event_title, attendees=None)
            system_message = f"Event created: {event_title} on {start_time}"
        except sr.UnknownValueError:
            system_message = "I'm sorry, I could not understand your response."
        except sr.RequestError:
            system_message = "Sorry, there was an error with the speech recognition service. Please try again later."
    else:
        system_message = "Failed to create event. Please try again with a valid date and time."

    if "delete the event" in user_message_lower:
        start_time, _ = parse_calendar_event_details(user_message)
        if start_time:
            event_to_delete = find_event(start_time)
            if event_to_delete:
                delete_event(event_to_delete['id'])
                system_message = "Sure thing, event deleted!"
            else:
                    system_message = "Failed to delete event. Event not found."
        else:
                system_message = "Failed to delete event. Please try again with a valid date and time."


    # START SEARCHING

    if "search for" in user_message.lower():
        search_query = re.sub(r'hey (adam|atom),?', '', transcript, flags=re.IGNORECASE).strip()
        search_query = search_query.replace("search for", "").strip()
        recipient_phone_number = config.RECIPIENT_PHONE_NUMBER
        search_results = search_google(search_query)
        source_urls = [result["link"] for result in search_results["items"]]
        snippets = [result["snippet"] for result in search_results["items"]]
    # enable below when twilio is working
    #     # sms_text = "Here are the source URLs for your search:\n" + "\n".join(str(url) for url in source_urls)
    #     # send_sms(sms_text, recipient_phone_number)

        gpt_search_prompt = f"Find the answer to the question '{search_query}' using the following search results snippets: \n\n" + "\n\n".join(snippets)

        search_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=gpt_search_prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.5,
        )

        answer = search_response["choices"][0]["text"].strip()

        if not source_urls:
            system_message = f"Sorry, I could not find any results for '{search_query}'"
        else:
            system_message = f"{answer} Check your texts for the sources!"

    messages.append(f"ATOM: {system_message}")

    # Generate and play audio (moved outside the else block)
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(system_message)

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("output.wav", format="wav")

    with open("pages/api/transcript.txt", "w") as f:
        f.write(system_message)  # Save the current message before playing the audio

    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

    chat_transcript = "\n".join(messages)
    print(f"Transcript: {chat_transcript}")

    return True  # Return True by default, indicating the script should


def listen_and_respond():
    is_listening = False
    is_playing_response = False
    while True:
        if not is_playing_response:
            with sr.Microphone() as source:
                r = sr.Recognizer()
                print("On standby...")
                try:
                    audio = r.listen(source, timeout=20)
                except sr.WaitTimeoutError:
                    continue

                try:
                    transcript = r.recognize_google(audio).lower()
                except sr.UnknownValueError:
                    transcript = ""
                    continue

                # START LISTEN

                if "hey atom" in transcript or "hey adam" in transcript:
                    is_listening = True

                # STOP LISTEN

                if "stop listening" in transcript:
                    is_listening = False
                    print("Ears are shut!")

                if is_listening:
                    with open("audio.wav", "wb") as f:
                        print("Generating audio response...")
                        f.write(audio.get_wav_data())  # Correct indentation here
                        print()

                    is_playing_response = True
                    should_continue = transcribe("audio.wav")
                    is_playing_response = False

                    if not should_continue:
                        is_listening = False

listen_and_respond()