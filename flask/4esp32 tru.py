from flask import Flask, request

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.data  # Directly read binary data
    if data:
        with open('C:/Users/Alienware/Music/AudioFiles/audio.wav', 'wb') as f:
            f.write(data)  # Write the data directly as binary
            print("File uploaded successfully")
            return "File uploaded successfully", 200
    else:
        print("No data received")
        return "No data received", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
