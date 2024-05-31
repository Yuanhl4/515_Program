from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'C:/Users/Alienware/Music/AudioFiles'
IMAGE_FOLDER = 'C:/Users/Alienware/Pictures'

@app.route('/upload', methods=['POST'])
def upload_file():
    filename = request.headers.get('X-Filename')  # Get the filename from the headers
    if not filename:
        return "Filename not provided", 400

    data = request.data  # Directly read binary data
    if data:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(data)  # Write the data directly as binary
            print("File uploaded successfully")
            return "File uploaded successfully", 200
    else:
        print("No data received")
        return "No data received", 400

@app.route('/get_image', methods=['GET'])
def get_image():
    image_path = os.path.join(IMAGE_FOLDER, 'image.bmp')
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/bmp')
    else:
        return "Image not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
