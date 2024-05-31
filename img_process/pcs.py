import os
import time
from PIL import Image
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Directories to monitor and process
watch_directory = r"C:\Users\Alienware\Pictures\text2image"
processed_directory = r"C:\Users\Alienware\Pictures\processed_image"

os.makedirs(processed_directory, exist_ok=True)

# Get the latest file
def get_latest_file(directory, extension=".png"):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]
    return max(files, key=os.path.getctime) if files else None

# Process and convert the image to BMP
def process_image(file_path, output_path):
    with Image.open(file_path) as img:
        img = img.resize((300, 300))
        img = img.convert("RGB")
        img.save(output_path, "BMP")
    print(f"Processed and saved image as: {output_path}")

# HTTP server to serve the BMP image
class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        latest_image = get_latest_file(processed_directory, ".bmp")
        if (latest_image):
            self.send_response(200)
            self.send_header("Content-type", "image/bmp")
            self.end_headers()
            with open(latest_image, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', 8080)  # Serve on all available interfaces, port 8080
    httpd = HTTPServer(server_address, CustomHandler)
    print("HTTP server running on port 8080...")
    httpd.serve_forever()

# Monitor the directory for new images and process them
def monitor_directory():
    last_processed = None
    while True:
        latest_file = get_latest_file(watch_directory, ".png")
        if latest_file and latest_file != last_processed:
            print(f"New image found: {latest_file}")
            processed_path = os.path.join(processed_directory, "latest_image.bmp")
            process_image(latest_file, processed_path)
            last_processed = latest_file
        time.sleep(5)

if __name__ == "__main__":
    from threading import Thread
    monitor_thread = Thread(target=monitor_directory)
    monitor_thread.start()

    run_server()
