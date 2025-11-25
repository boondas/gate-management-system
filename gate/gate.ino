#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Flask Server Endpoint (Render)
const char* serverUrl = "https://gate-management-system-pe2o.onrender.com/validate_user";

// SIM900 Pins (ESP32)
#define RXD2 16
#define TXD2 17

// Relay pin
#define RELAY_PIN 2

WiFiManager wifiManager;

void sendATCommand(const char* command) {
  Serial2.println(command);
  delay(1500);  // Reliable response timing
}

void hangUpCall() {
  sendATCommand("ATH");
  Serial.println("Call Hung Up");
}

String extractPhoneNumber(String sim900Response) {
  int clipIndex = sim900Response.indexOf("+CLIP:");
  if (clipIndex == -1) return "";

  int start = sim900Response.indexOf("\"", clipIndex);
  if (start == -1) return "";
  start += 1;

  int end = sim900Response.indexOf("\"", start);
  if (end == -1) return "";

  String rawPhone = sim900Response.substring(start, end);

  // Normalize: if no +, assume +27 (South Africa)
  if (!rawPhone.startsWith("+")) {
    if (rawPhone.startsWith("0")) {
      rawPhone = "+27" + rawPhone.substring(1);
    } else if (rawPhone.length() == 9) {
      rawPhone = "+27" + rawPhone;  // e.g., 786384899 → +27786384899
    } else {
      return "";  // Invalid
    }
  }

  return rawPhone;
}

String urlEncodePlus(String phone) {
  phone.replace("+", "%2B");
  return phone;
}

void validatePhoneNumber(String phoneNumber) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }

  // Reduce WiFi power to avoid current spike
  WiFi.setTxPower(WIFI_POWER_8_5dBm);

  HTTPClient http;
  String encodedPhone = urlEncodePlus(phoneNumber);
  String url = String(serverUrl) + "?phone_number=" + encodedPhone;

  Serial.println("Requesting: " + url);

  http.begin(url);
  http.setTimeout(10000);  // 10 sec for Render wake-up
  int httpCode = http.GET();

  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Server Response: " + response);

    StaticJsonDocument<250> doc;
    DeserializationError error = deserializeJson(doc, response);
    if (error) {
      Serial.println("JSON parse error: " + String(error.c_str()));
    } else {
      String status = doc["status"] | "INVALID";
      if (status == "VALID") {
        Serial.println("ACCESS GRANTED");
        digitalWrite(RELAY_PIN, HIGH);
        delay(5000);  // Keep gate open 5 sec
        digitalWrite(RELAY_PIN, LOW);
      } else {
        Serial.println("ACCESS DENIED");
      }
    }
  } else {
    Serial.println("HTTP Error: " + String(httpCode));
    if (httpCode == 404) {
      Serial.println("Tip: Visit your Render URL in browser to wake it up!");
    }
  }

  http.end();
  WiFi.setTxPower(WIFI_POWER_19_5dBm);  // Restore full power
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  // WiFiManager - creates AP if no WiFi
  wifiManager.setConfigPortalTimeout(180);  // 3 min
  if (!wifiManager.autoConnect("ESP32-Gate-AP", "gate1234")) {
    Serial.println("Failed to connect. Restarting...");
    delay(3000);
    ESP.restart();
  }
  Serial.println("Connected to WiFi");

  // SIM900 Init
  sendATCommand("AT");
  sendATCommand("ATE0");        // Echo off
  sendATCommand("AT+CLIP=1");   // Caller ID
  sendATCommand("AT+CMGF=1");   // SMS text mode (optional)
}

void loop() {
  static String buffer = "";

  while (Serial2.available()) {
    char c = Serial2.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        Serial.println("SIM900: " + buffer);
        
        if (buffer.indexOf("+CLIP:") != -1) {
          String phone = extractPhoneNumber(buffer);
          if (phone.length() > 0) {
            Serial.println("Incoming Call: " + phone);
            hangUpCall();
            Serial.println("Waiting 2s for GSM to settle...");
            delay(2000);
            validatePhoneNumber(phone);
          } else {
            Serial.println("Failed to parse phone from: " + buffer);
            hangUpCall();
          }
        }
        buffer = "";
      }
    } else if (c >= 32 && c <= 126) {
      buffer += c;
    }
  }

  delay(100);
}