import streamlit as st
import os

TRANSCRIPTION_DIRECTORY = 'C:/Users/Alienware/Documents/transcriptions'
IMAGE_OUTPUT_DIRECTORY = 'C:/Users/Alienware/Pictures/text2image'

def get_latest_transcription():
    transcription_files = [f for f in os.listdir(TRANSCRIPTION_DIRECTORY) if f.endswith(".txt")]
    if not transcription_files:
        return None, None
    latest_file = max(transcription_files, key=lambda x: os.path.getmtime(os.path.join(TRANSCRIPTION_DIRECTORY, x)))
    with open(os.path.join(TRANSCRIPTION_DIRECTORY, latest_file), 'r') as file:
        transcription = file.read()
    return latest_file, transcription

def load_latest_image(timestamp):
    images = [f for f in os.listdir(IMAGE_OUTPUT_DIRECTORY) if f.endswith(".png") and timestamp in f]
    if not images:
        return None
    latest_image = max(images, key=lambda x: os.path.getmtime(os.path.join(IMAGE_OUTPUT_DIRECTORY, x)))
    return os.path.join(IMAGE_OUTPUT_DIRECTORY, latest_image)

def display_data(transcription, image_path):
    st.markdown("<h1 style='text-align: center;'>E-Note</h1>", unsafe_allow_html=True)
    
    st.markdown(f"<h4 style='color: white; text-align: center; line-height: 1.6;'>{transcription}</h4>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)  # Add space between transcription and image
    
    if image_path:
        st.image(image_path, width=300, use_column_width=True)
    else:
        st.write("No images found for this transcription.")

def main():
    st.cache_data.clear()  # Clear cache to ensure latest data is fetched
    transcription_file, transcription = get_latest_transcription()
    if transcription_file:
        timestamp = transcription_file.split('-')[1].split('.')[0]
        latest_image_path = load_latest_image(timestamp)
        display_data(transcription, latest_image_path)
    else:
        st.write("No transcriptions found.")

# Custom CSS for a high-end design feel
st.markdown(
    """
    <style>
    .main {
        background-color: #000000;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
    }
    .stApp {
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        background-color: #000000;
        color: white;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
    }
    .stImage img {
        border-radius: 10px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if __name__ == '__main__':
    main()
