import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
from flask import Flask, send_file, abort

# Configuration
SOURCE_IMAGE_DIR = r"C:\Users\Alienware\Pictures\text2image"
PROCESSED_IMAGE_DIR = r"C:\Users\Alienware\Pictures\processed_image"
OUTPUT_IMAGE = os.path.join(PROCESSED_IMAGE_DIR, "output_image.xbm")
HOST = '0.0.0.0'
PORT = 8000

# Flask setup
app = Flask(__name__)

def get_newest_image_path(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".png")]
    if not files:
        return None
    newest_file = max(files, key=os.path.getctime)
    return newest_file

class NewImageHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".png"):
            print(f"New PNG file detected: {event.src_path}")
            self.process_new_image(event.src_path)

    def process_new_image(self, image_path):
        try:
            print(f"Processing image: {image_path}")
            img = Image.open(image_path).convert('1')  # Convert to 1-bit pixels
            img = img.resize((128, 128))  # Resize to 128x128 pixels
            img.save(OUTPUT_IMAGE, format='xbm')
            print(f"Processed and saved new image to: {OUTPUT_IMAGE}")

            # Print the byte array for debugging
            with open(OUTPUT_IMAGE, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('#define'):
                        continue
                    if line.startswith('static'):
                        break
                    line = line.strip().replace('0x', '').replace(',', '')
                    print(line, end='')

        except Exception as e:
            print(f"Failed to process image: {image_path}, error: {e}")

@app.route('/get_image', methods=['GET'])
def get_image():
    if os.path.exists(OUTPUT_IMAGE):
        print(f"Serving image: {OUTPUT_IMAGE}")
        return send_file(OUTPUT_IMAGE, mimetype='image/x-xbitmap')
    else:
        print(f"File not found: {OUTPUT_IMAGE}")
        return abort(404, description="Image not found")

def start_observer():
    event_handler = NewImageHandler()
    observer = Observer()
    observer.schedule(event_handler, path=SOURCE_IMAGE_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
            newest_image = get_newest_image_path(SOURCE_IMAGE_DIR)
            if newest_image:
                event_handler.process_new_image(newest_image)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    # Ensure the processed image directory exists
    os.makedirs(PROCESSED_IMAGE_DIR, exist_ok=True)

    # Start file observer in a separate thread
    from threading import Thread
    observer_thread = Thread(target=start_observer)
    observer_thread.start()

    # Start Flask server
    app.run(host=HOST, port=PORT)
