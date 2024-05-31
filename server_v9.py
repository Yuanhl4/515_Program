import os
import time
import base64
import json
import urllib.request
from datetime import datetime
from google.cloud import speech
from google.cloud.speech import RecognitionAudio, RecognitionConfig
from pydub.utils import mediainfo

# Google Cloud Speech client setup
client = speech.SpeechClient()

# Directories setup
AUDIO_FILES_DIRECTORY = 'C:/Users/Alienware/Music/AudioFiles'
IMAGE_OUTPUT_DIRECTORY = 'C:/Users/Alienware/Pictures/text2image'
TRANSCRIPTION_DIRECTORY = 'C:/Users/Alienware/Documents/transcriptions'
os.makedirs(IMAGE_OUTPUT_DIRECTORY, exist_ok=True)
os.makedirs(TRANSCRIPTION_DIRECTORY, exist_ok=True)

webui_server_url = 'http://127.0.0.1:7860'  # Base URL for the web UI server

def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def decode_and_save_base64(base64_str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))

def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))

def transcribe_audio(file_path):
    media_info = mediainfo(file_path)
    sample_rate = int(media_info['sample_rate'])

    with open(file_path, "rb") as audio_file:
        content = audio_file.read()
    audio = RecognitionAudio(content=content)
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US"
    )
    response = client.recognize(config=config, audio=audio)
    return ' '.join([result.alternatives[0].transcript for result in response.results])

def call_txt2img_api(prompt):
    response = call_api('sdapi/v1/txt2img', prompt=prompt, width=300, height=300, steps=50, cfg_scale=7.5)
    images = []
    for index, image in enumerate(response.get('images', [])):
        save_path = os.path.join(IMAGE_OUTPUT_DIRECTORY, f'image-{timestamp()}-{index}.png')
        print(f"Saving image to: {save_path}")
        decode_and_save_base64(image, save_path)
        images.append(save_path)
    return images

def save_transcription(transcription):
    save_path = os.path.join(TRANSCRIPTION_DIRECTORY, f'transcription-{timestamp()}.txt')
    with open(save_path, 'w') as file:
        file.write(transcription)
    return save_path

def monitor_directory():
    last_processed_time = None
    file_path = os.path.join(AUDIO_FILES_DIRECTORY, 'audio.wav')
    while True:
        if os.path.exists(file_path):
            current_modified_time = os.path.getmtime(file_path)
            if last_processed_time is None or current_modified_time > last_processed_time:
                file_size = os.path.getsize(file_path)
                expected_size = 44 + 15000 * 3 * 2
                if file_size == expected_size:
                    transcription = transcribe_audio(file_path)
                    print(f"Transcription: {transcription}")
                    images = call_txt2img_api(transcription)
                    transcription_path = save_transcription(transcription)
                    last_processed_time = current_modified_time
                else:
                    print(f"File size mismatch: {file_size} != {expected_size}")
        time.sleep(10)

if __name__ == '__main__':
    monitor_directory()
