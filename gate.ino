#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Flask Server Endpoint
const char* serverUrl = "https://web-production-168b.up.railway.app//validate_user";

// SIM900 Configuration
#define RXD2 16
#define TXD2 17

// Relay pin
#define RELAY_PIN 2

WiFiManager wifiManager;

// Function to send AT commands to the SIM900 module
void sendATCommand(const char* command) {
  Serial2.println(command);
  delay(1000); // Wait for the command to process
}

// Function to read responses from the SIM900 module
String readSIM900() {
  String response = "";
  while (Serial2.available()) {
    char c = Serial2.read();
    response += c;
  }
  return response;
}

// Function to normalize phone numbers
String normalizePhoneNumber(String phoneNumber) {
  phoneNumber.replace(" ", ""); // Remove spaces
  phoneNumber.replace("-", ""); // Remove dashes
  if (phoneNumber.startsWith("0")) {
    phoneNumber = "+27" + phoneNumber.substring(1); // Convert to +27 format
  }
  if (!phoneNumber.startsWith("+")) {
    phoneNumber = "+" + phoneNumber;
  }
  return phoneNumber;
}

// Function to extract phone numbers from SIM900 responses
String extractPhoneNumber(String sim900Response) {
  int start = sim900Response.indexOf("\"") + 1;
  int end = sim900Response.indexOf("\"", start);
  String phoneNumber = sim900Response.substring(start, end);
  phoneNumber = normalizePhoneNumber(phoneNumber);
  return phoneNumber;
}

// Function to hang up an incoming call
void hangUpCall() {
  sendATCommand("ATH"); // Send ATH command to hang up the call
  Serial.println("Call Hung Up");
}

// Function to validate phone numbers with the Flask server
void validatePhoneNumber(String phoneNumber) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "?phone_number=" + phoneNumber;

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      Serial.println("Validation Response: " + payload);

      // Parse JSON response
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);

      if (error) {
        Serial.print("JSON Parsing Failed: ");
        Serial.println(error.c_str());
        return;
      }

      const char* status = doc["status"];
      Serial.print("Status: ");
      Serial.println(status);

      if (String(status) == "VALID") {
        // Grant Access
        Serial.println("Access Granted");
        digitalWrite(RELAY_PIN, HIGH); // Activate relay
        delay(5000);                  // Keep the relay active for 5 seconds
        digitalWrite(RELAY_PIN, LOW); // Deactivate relay
      } else {
        Serial.println("Access Denied");
      }
    } else {
      Serial.println("HTTP Request Failed with Code: " + String(httpCode));
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void setup() {
  // Serial and SIM900 Configuration
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  // Configure Relay Pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // Ensure the relay is off initially

  // Initialize WiFi Manager
  wifiManager.autoConnect("ESP32-Gate-Manager");

  Serial.println("WiFi Connected: " + WiFi.SSID());

  // Initialize SIM900
  sendATCommand("AT");            // Check communication
  sendATCommand("ATE0");          // Disable echo
  sendATCommand("AT+CLIP=1");     // Enable caller ID notification
}

void loop() {
  if (Serial2.available()) {
    String sim900Response = readSIM900();
    Serial.println("SIM900 Response: " + sim900Response);

    // Check for incoming call
    if (sim900Response.indexOf("+CLIP:") != -1) {
      String phoneNumber = extractPhoneNumber(sim900Response);
      Serial.println("Incoming Call from: " + phoneNumber);

      // Hang up the call
      hangUpCall();

      // Validate the phone number with Flask
      validatePhoneNumber(phoneNumber);
    }
  }

  delay(1000); // Delay to avoid overloading the SIM900 module
}
