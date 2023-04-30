import io
import cv2
import numpy as np
from PIL import ImageGrab
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import config as config
import openai
import numpy as np
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from pydub import AudioSegment
import simpleaudio as sa
from elevenlabslib import ElevenLabsUser
api_key = config.ELEVEN_LABS_API_KEY
user = ElevenLabsUser(api_key)
from PIL import Image


# Initialize Azure Computer Vision client
computervision_client = ComputerVisionClient(config.AZURE_ENDPOINT, CognitiveServicesCredentials(config.AZURE_API_KEY))

def analyze_screen_and_respond():
    tags, text = analyze_screen()
    print(tags, text)
    gpt_prompt = f"Find a concise answer to the question 'What is on my screen?' based on the following tags: {', '.join(tags)} and the extracted text: {text}"

    # Generate audio response from GPT
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=gpt_prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )

    system_message = response["choices"][0]["text"].strip()

    # Generate and play audio response
    voice = user.get_voices_by_name("Antoni")[0]
    audio = voice.generate_audio_bytes(system_message)

    audio = AudioSegment.from_file(io.BytesIO(audio), format="mp3")
    audio.export("output.wav", format="wav")

    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

    return system_message



def analyze_screen():
    # Capture the screen
    screen = capture_screen()

    # Convert the OpenCV image format to the PIL image format
    pil_image = Image.fromarray(np.uint8(screen))

    # Save the image as a temporary file
    pil_image.save('temp_screen_capture.png')

    # Load the temporary file as an in-memory stream
    with open('temp_screen_capture.png', 'rb') as image_stream:
        ocr_result = computervision_client.recognize_printed_text_in_stream(image_stream)

    # Extract tags and text from the OCR result
    tags, text = extract_tags_and_text(ocr_result)

    return tags, text

def capture_screen():
    # Capture the screen using PIL.ImageGrab
    pil_image = ImageGrab.grab()

    # Resize the image to a smaller size
    max_size = (1920, 1080)  # You can change these values to the desired dimensions
    pil_image.thumbnail(max_size, Image.ANTIALIAS)

    # Convert the PIL image format to the OpenCV image format
    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    return opencv_image



def extract_tags_and_text(ocr_result):
    tags = []
    text = ""

    for region in ocr_result.regions:
        for line in region.lines:
            for word in line.words:
                text += word.text + " "
                if word.text.lower() not in tags:
                    tags.append(word.text.lower())

    return tags, text.strip()
