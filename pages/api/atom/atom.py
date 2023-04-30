from elevenlabslib import ElevenLabsUser
import datetime
import openai
from elevenlabslib import *
from pydub.playback import play
from search import search_google
import os
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain.agents import load_tools
from google_cal import create_event, delete_event, find_event, get_events, parse_calendar_event_details, play_ask_event_title
from gmail import announce_unread_emails, create_draft_email
import re
import config as config
import speech_recognition as sr
from datetime import timedelta
from pydub import AudioSegment
from twilio_utils import send_sms
from screen_capture import analyze_screen, analyze_screen_and_respond
import os
import io
import simpleaudio as sa
from google_docs import create_google_doc, play_ask_doc_title

os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY

openai.api_key = config.OPENAI_API_KEY
api_key = config.ELEVEN_LABS_API_KEY
user = ElevenLabsUser(api_key)

messages = [
    "You are an AI executive assistant named ATOM (can be pronounced as Adam). Provide responses less than 15 words."]

# INTRO MESSAGE


# def play_intro_message():
#     voice = user.get_voices_by_name("Antoni")[0]
#     audio = voice.generate_audio_bytes(
#         "Hello, I'm ATOM, your AI executive assistant. How can I help you today?")
#     audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
#     audio.export("intro.wav", format="wav")

#     wave_obj = sa.WaveObject.from_wave_file("intro.wav")
#     play_obj = wave_obj.play()
#     play_obj.wait_done()


# play_intro_message()


def commands(audio):
    global messages

    start_time = None
    end_time = None

    audio_file = open(audio, "rb")
    print(f"Audio file size: {os.path.getsize(audio)} bytes")
    print("Transcribing audio...")
    transcript_response = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = transcript_response['text'].strip()
    user_message = transcript.strip()

    prompt = messages[-1]
    prompt += f"\nUser: {user_message}"

    if "stop listening" in user_message.lower():
        return False

    user_message_lower = user_message.lower()

    # SCREEN VIEW

    if "what's on my screen" in user_message_lower:
        system_message = analyze_screen_and_respond()

    # CALENDAR COMMANDS

    if any(phrase in user_message_lower for phrase in ["create an event", "schedule an event", "make time for"]):
        start_time, end_time = parse_calendar_event_details(user_message)
    if start_time and end_time:
        # Prompt the user to say the event title
        system_message = "Sure thing! What would the event title be?"
        with open("pages/api/transcript.txt", "w") as f:
            # Save the current message before playing the audio
            f.write(system_message)
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

            # Send SMS
            recipient_phone_number = config.RECIPIENT_PHONE_NUMBER
            sms_text = f"New calendar event: '{event_title}' on {start_time.strftime('%Y-%m-%d %I:%M %p')}"
            send_sms(sms_text, recipient_phone_number)

        except sr.UnknownValueError:
            system_message = "I'm sorry, I could not understand your response."
        except sr.RequestError:
            system_message = "Sorry, there was an error with the speech recognition service. Please try again later."

    if any(phrase in user_message_lower for phrase in ["delete the event", "remove the event", "cancel the event"]):
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

    if any(phrase in user_message_lower for phrase in ["list upcoming events today", "list today's events", "list events today", "list upcoming events"]):
        events = get_events()
        today = datetime.datetime.now().date()
        todays_events = [
            event for event in events if event['start_time'].date() == today]
        if todays_events:
            system_message = "Looks like you got:\n"
            for event in todays_events:
                start = event['start_time'].strftime("%I:%M %p")
                end = event['end_time'].strftime("%I:%M %p")
                summary = event['summary']
                system_message += f"{start} - {end}: {summary}\n"
            # Send SMS
            recipient_phone_number = config.RECIPIENT_PHONE_NUMBER
            sms_text = system_message
            send_sms(sms_text, recipient_phone_number)
            # system_message = "Here are your upcoming events for today. Check your texts for the details!"
        else:
            system_message = "All clear! No upcoming events for today."

    # START SEARCHING

    if any(phrase in user_message_lower for phrase in ["search for", "look up"]):
        search_query = transcript.replace("search for", "").replace(
            "hey adam,", "").replace("hey atom,", "").replace("provide the sources", "").strip()
        recipient_phone_number = config.RECIPIENT_PHONE_NUMBER
        search_results = search_google(search_query)
        print("Search results:", search_results)

        snippets = [result["snippet"] for result in search_results["items"]]
        gpt_search_prompt = f"Find a concise answer to the question '{search_query}' using the following search results snippets: \n\n" + "\n\n".join(
            snippets)

        search_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=gpt_search_prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.5,
        )
        print("GPT response:", search_response)

        answer = search_response["choices"][0]["text"].strip()

        if "provide the sources" in user_message_lower:
            source_list = []
            for result in search_results["items"]:
                source = f"{result['title']} - {result['link']}"
                source_list.append(source)

            if not source_list:
                system_message = f"Sorry, I could not find any results for '{search_query}'"
            else:
                formatted_sources = "\n\n".join(source_list)
                sms_text = f"Here are the source URLs for your search:\n\n{formatted_sources}"
                system_message = f"{answer} Check your texts for the sources!"
                send_sms(sms_text, recipient_phone_number)
                print("SMS sent.")

        else:
            system_message = f"{answer}."

        messages.append(f"ATOM: {system_message}")

    # CREATE DRAFTS IN GOOGLE DOCS

    if "create a draft" in user_message_lower:
        draft_query = transcript.replace("create a draft", "").replace(
            "hey adam,", "").replace("hey atom,", "").strip()

        system_message = "Okay, what would the draft title be?"
        with open("pages/api/transcript.txt", "w") as f:
            # Save the current message before playing the audio
            f.write(system_message)
        play_ask_doc_title()
        print(system_message)

        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            title = recognizer.recognize_google(audio)

            # Generate the initial text using GPT
            draft_prompt = f"Write an initial draft text about '{draft_query}' and for the document titled '{title}':"
            draft_response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=draft_prompt,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.5,
            )
            initial_text = draft_response["choices"][0]["text"].strip()

            document_id = create_google_doc(title, initial_text)

            # SEND SMS
            if document_id:
                system_message = f"Created a new Google Doc with title '{title}'."
                # Send the document link via SMS
                doc_link = f"https://docs.google.com/document/d/{document_id}"
                sms_text = f"Here's the link to the newly created Google Doc: {doc_link}"
                recipient_phone_number = config.RECIPIENT_PHONE_NUMBER
                send_sms(sms_text, recipient_phone_number)
            else:
                system_message = "Failed to create a new Google Doc. Please try again later."
        except sr.UnknownValueError:
            system_message = "I'm sorry, I could not understand your response."
        except sr.RequestError:
            system_message = "Sorry, there was an error with the speech recognition service. Please try again later."

    # Generate and play audio (moved outside the else block)
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(system_message)

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("output.wav", format="wav")

    with open("pages/api/transcript.txt", "w") as f:
        # Save the current message before playing the audio
        f.write(system_message)

    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

    chat_transcript = "\n".join(messages)
    print(f"Transcript: {chat_transcript}")

    return True  # Return True by default, indicating the script should


def transcribe(audio):
    global messages

    audio_file = open(audio, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    prompt = messages[-1]
    prompt += f"\nUser: {transcript['text']}"

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=80,
        n=1,
        stop=None,
        temperature=0.5,
    )

    if "stop listening" in transcript['text'].lower():
        return False  # Return False when the keyword is detected

    system_message = response["choices"][0]["text"]
    system_message = system_message.replace(
        "Alice:", "").replace("ATOM:", "").strip()
    messages.append(f"{system_message}")

    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(system_message)

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("output.wav", format="wav")

    with open("pages/api/transcript.txt", "w") as f:
        # Save the current message before playing the audio
        f.write(system_message)

    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

    chat_transcript = "\n".join(messages)
    print(f"Transcript: {chat_transcript}")

    return True  # Return True by default, indicating the script should continue running


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
                        # Correct indentation here
                        f.write(audio.get_wav_data())
                        print()

                    is_playing_response = True

                    if "what's on my screen" in transcript:
                        should_continue = analyze_screen_and_respond()
                    elif any(command in transcript for command in ["look at my screen", "create an event", "make time for", "schedule an event", "delete the event", "remove the event", "get rid of the event", "search for", "list upcoming events today", "list today's events", "list upcoming events", "list events today", "be quiet", "look up", "create a draft"]):
                        should_continue = commands("audio.wav")
                    else:
                        should_continue = transcribe("audio.wav")

                    is_playing_response = False

                    if not should_continue:
                        is_listening = False


listen_and_respond()
