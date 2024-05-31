#include <Arduino.h>
#include <FS.h>
#include <SPIFFS.h>
#include "WiFi.h"
#include "ESPAsyncWebServer.h"
#include <HTTPClient.h>
#include <Adafruit_NeoPixel.h>

const char* ssid = "iPhone(Alter)";
const char* password = "12341234";
const char* serverUrl = "http://192.168.15.97:8000/upload";

AsyncWebServer server(80);

const int sampleWindow = 3000;  // Sample window width in mS (50 mS = 20Hz)
const int sampleRate = 15000; // Sample rate in Hz
const int numSamples = sampleRate * sampleWindow / 1000;
const int AMP_PIN = A3;       // Preamp output pin connected to A0

#define NEOPIXEL_PIN 38       // NeoPixel LED pin
#define NUMPIXELS 1           // Number of NeoPixels

Adafruit_NeoPixel strip(NUMPIXELS, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

int16_t* buffer = nullptr;

void setNeoPixelColor(uint8_t r, uint8_t g, uint8_t b) {
    strip.setPixelColor(0, strip.Color(r, g, b));
    strip.show();
}

void writeUInt32(File &file, uint32_t value) {
    byte buf[4];
    buf[0] = value & 0xFF;
    buf[1] = (value >> 8) & 0xFF;
    buf[2] = (value >> 16) & 0xFF;
    buf[3] = (value >> 24) & 0xFF;
    file.write(buf, 4);
}

void writeUInt16(File &file, uint16_t value) {
    byte buf[2];
    buf[0] = value & 0xFF;
    buf[1] = (value >> 8) & 0xFF;
    file.write(buf, 2);
}

void writeWAVHeader(File file, int numSamples, int actualSampleRate) {
    Serial.println("Starting WAV Header Write:");
    long startPos = file.position();

    // Calculate byte rate based on actual sample rate
    uint32_t byteRate = actualSampleRate * sizeof(int16_t);
    uint32_t dataSize = numSamples * sizeof(int16_t);

    // Write header manually byte-by-byte
    file.write((const uint8_t*)"RIFF", 4);
    writeUInt32(file, 36 + dataSize);  // dataSize
    file.write((const uint8_t*)"WAVE", 4);
    file.write((const uint8_t*)"fmt ", 4);
    writeUInt32(file, 16);  // subchunk1Size
    writeUInt16(file, 1);   // PCM audio format
    writeUInt16(file, 1);   // numChannels
    writeUInt32(file, actualSampleRate);  // sampleRate
    writeUInt32(file, byteRate);  // byteRate
    writeUInt16(file, 2);   // blockAlign
    writeUInt16(file, 16);  // bitsPerSample
    file.write((const uint8_t*)"data", 4);
    writeUInt32(file, dataSize);  // dataSize

    long endPos = file.position();
    Serial.print("End WAV Header Write, Bytes Written: ");
    Serial.println(endPos - startPos);
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());

    if (!SPIFFS.begin(true)) {
        Serial.println("An Error has occurred while mounting SPIFFS");
        return;
    }

    buffer = new int16_t[numSamples]; // Allocate buffer dynamically
    if (!buffer) {
        Serial.println("Failed to allocate memory for audio buffer");
        return;
    }

    // Initialize NeoPixel
    strip.begin();
    strip.show(); // Initialize all pixels to 'off'
}

void loop() {
    unsigned long startTime = millis();
    unsigned long loopStartTime;

    if (!buffer) {
        Serial.println("Buffer not allocated, skipping loop");
        delay(1000);
        return;
    }
    
    setNeoPixelColor(0, 255, 0); // Green light for recording
    Serial.println("Starting recording...");
    loopStartTime = millis(); // Record loop start time
    
    int i = 0;
    while (millis() - startTime < sampleWindow) {
        if (i < numSamples) {
            buffer[i] = analogRead(AMP_PIN) - 512;  // Assuming 0-1023 input range
            i++;
        }
    }

    unsigned long loopEndTime = millis(); // Record loop end time
    Serial.print("Loop execution time: ");
    Serial.println(loopEndTime - loopStartTime);

    Serial.println("Recording ended.");
    Serial.print("Recorded Samples: ");
    Serial.println(i);  // Check how many samples were actually recorded

    // Save to SPIFFS
    File file = SPIFFS.open("/audio.wav", "w");  // Overwrite if existing
    if (!file) {
        Serial.println("Failed to open file for writing");
        return;
    }

    // Write header and data to file
    writeWAVHeader(file, i, sampleRate); // Pass actual recorded samples count and sample rate
    file.write((const uint8_t*)buffer, i * sizeof(int16_t)); // Write actual recorded samples
    file.close();


    // Reopen for reading to debug
    file = SPIFFS.open("/audio.wav", "r");
    if (!file) {
        Serial.println("Failed to open file for reading");
        return;
    }

    size_t fileSize = file.size();
    Serial.print("Actual file size: ");
    Serial.println(fileSize);
    file.close();

    size_t expectedSize = 44 + i * sizeof(int16_t);
    Serial.print("Expected file size: ");
    Serial.println(expectedSize);

    if (fileSize != expectedSize) {
        Serial.println("File size mismatch!");
        setNeoPixelColor(255, 255, 255); // White light for 0.5 seconds as a reminder
        delay(500);
    } else {
        Serial.println("File size correct.");
        file = SPIFFS.open("/audio.wav", "r");
        if (!file) {
            Serial.println("Failed to reopen file for reading");
            return;
        }

        HTTPClient http;
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/octet-stream");
        int httpResponseCode = http.sendRequest("POST", &file, file.size());

        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);

        http.end();
        file.close();

        if (httpResponseCode == 200) {
            setNeoPixelColor(255, 0, 0); // Green light for successful upload
            delay(5000); // Keep green light on for 5 seconds
            esp_deep_sleep_start(); // Enter deep sleep
        } else {
            setNeoPixelColor(255, 255, 255); // White light for 0.5 seconds as a reminder
            delay(500);
        }
    }

    // Reset the buffer for the next recording
    delete[] buffer;
    buffer = new int16_t[numSamples];
    if (!buffer) {
        Serial.println("Failed to reallocate memory for audio buffer");
        return;
    }

    delay(5000);  // Delay to prevent watchdog timer reset
}
