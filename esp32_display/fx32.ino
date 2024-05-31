#include <WiFi.h>
#include <HTTPClient.h>
#include <GxEPD2_BW.h>
#include <SPIFFS.h>

// Display and WiFi credentials
#define SSID "iPhone(Alter)"
#define PASSWORD "12341234"
const char* serverName = "http://192.168.15.97:8080";

// E-paper display initialization
#define GxEPD2_DRIVER_CLASS GxEPD2_420_GDEY042T81 // GDEY042T81 400x300, SSD1683 (no inking)
GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(GxEPD2_420_GDEY042T81(/*CS=5*/ SS, /*DC=*/ 17, /*RST=*/ 16, /*BUSY=*/ 4));

// File path for the downloaded image
const char* bmpFilePath = "/latest_image.bmp";

void setup() {
  Serial.begin(115200);
  // Initialize SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("An error has occurred while mounting SPIFFS");
    return;
  }
  // Initialize the display
  display.init();
  // Connect to WiFi
  connectToWiFi();
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Download the BMP image
    if (downloadImage(bmpFilePath)) {
      // Display the image
      displayImage(bmpFilePath);
    }
  } else {
    connectToWiFi();
  }
  // Wait for some time before checking again
  delay(30000); // Check every 30 seconds
}

void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("Connected to WiFi");
}

bool downloadImage(const char* path) {
  HTTPClient http;
  http.begin(serverName);
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    File file = SPIFFS.open(path, FILE_WRITE);
    if (!file) {
      Serial.println("Failed to open file for writing");
      return false;
    }
    http.writeToStream(&file);
    file.close();
    Serial.println("Image downloaded successfully");
    return true;
  } else {
    Serial.printf("Failed to download image, HTTP code: %d\n", httpCode);
    return false;
  }
  http.end();
}

void displayImage(const char* path) {
  File file = SPIFFS.open(path, FILE_READ);
  if (!file) {
    Serial.println("Failed to open file for reading");
    return;
  }
  display.setFullWindow();
  display.firstPage();
  do {
    drawBitmapFromSPIFFS(path, 0, 0);
  } while (display.nextPage());
  file.close();
  Serial.println("Image displayed successfully");
}

void drawBitmapFromSPIFFS(const char* filename, int16_t x, int16_t y) {
  File file = SPIFFS.open(filename, FILE_READ);
  if (!file) {
    Serial.print("File not found: ");
    Serial.println(filename);
    return;
  }

  if (read16(file) == 0x4D42) {
    uint32_t fileSize = read32(file);
    (void)read32(file); // ignore creator bytes
    uint32_t imageOffset = read32(file);
    uint32_t headerSize = read32(file);
    uint32_t width = read32(file);
    uint32_t height = read32(file);
    uint16_t planes = read16(file);
    uint16_t depth = read16(file);
    uint32_t format = read32(file);

    if ((planes == 1) && (format == 0)) {
      y += height - 1;
      bool flip = true;
      uint32_t rowSize = (width * 3 + 3) & ~3;
      if (height < 0) {
        height = -height;
        flip = false;
      }
      if (depth == 24 && format == 0) {
        uint8_t sdbuffer[3*20];
        uint8_t buffidx = sizeof(sdbuffer);
        file.seek(imageOffset);
        for (uint16_t row = 0; row < height; row++) {
          uint32_t pos = flip ? imageOffset + (height - 1 - row) * rowSize : imageOffset + row * rowSize;
          file.seek(pos);
          for (uint16_t col = 0; col < width; col++) {
            if (buffidx >= sizeof(sdbuffer)) {
              file.read(sdbuffer, sizeof(sdbuffer));
              buffidx = 0;
            }
            uint8_t b = sdbuffer[buffidx++];
            uint8_t g = sdbuffer[buffidx++];
            uint8_t r = sdbuffer[buffidx++];
            uint16_t color = rgbToGrayscale(r, g, b);
            display.drawPixel(x + col, y - row, color);
          }
        }
      }
    }
  }
  file.close();
}

uint16_t rgbToGrayscale(uint8_t r, uint8_t g, uint8_t b) {
  // Use the luminance formula to convert RGB to grayscale
  return (r * 0.299 + g * 0.587 + b * 0.114) > 128 ? GxEPD_WHITE : GxEPD_BLACK;
}

uint16_t read16(File &f) {
  uint16_t result;
  ((uint8_t *)&result)[0] = f.read();
  ((uint8_t *)&result)[1] = f.read();
  return result;
}

uint32_t read32(File &f) {
  uint32_t result;
  ((uint8_t *)&result)[0] = f.read();
  ((uint8_t *)&result)[1] = f.read();
  ((uint8_t *)&result)[2] = f.read();
  ((uint8_t *)&result)[3] = f.read();
  return result;
}
