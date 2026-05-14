#include <SPIFFS.h>
#include <WiFi.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <time.h>
#include <ArduinoJson.h>

// ===== WiFi Configuration =====
const char* WIFI_SSID_DEFAULT = "your_wifi_ssid";
const char* WIFI_PASSWORD_DEFAULT = "your_wifi_password";

// ===== MQTT Broker Configuration =====
const char* MQTT_HOST = "your_vps_ip";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "sensor_user";
const char* MQTT_PASSWORD = "123456";

// ===== Device Identification =====
const char* SENSOR_ID = "esp32_devkit_v1";
const char* LOCATION = "Lab";

// ===== MQTT Topics (standardized) =====
const char* MQTT_PUBLISH_TOPIC = "sensors/esp32_devkit_v1/data";
const char* MQTT_SUBSCRIBE_TOPIC = "ptdl/devices/esp32_devkit_v1/commands";

// ===== Pin Configuration =====
#define DHT_PIN 4      // DHT11 data pin
#define FAN_PIN 32     // Fan relay GPIO32
#define FOG_PIN 33     // Fog/Mist relay GPIO33
#define LAMP_PIN 25    // Lamp relay GPIO25

// ===== Sensor Setup =====
#define DHTTYPE DHT11
DHT dht(DHT_PIN, DHTTYPE);

// ===== MQTT Client =====
WiFiClient espClient;
PubSubClient mqttClient(espClient);
Preferences preferences;
String wifiSsid;
String wifiPassword;

// ===== Timing Variables =====
unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL = 5000;  // Publish every 5 seconds

// ===== Function Prototypes =====
void setupWiFi();
void connectMQTT();
void publishSensorData();
void onMqttMessage(char* topic, byte* payload, unsigned int length);
void setRelayState(int pin, bool state);
void parseAndExecuteCommand(const char* payload);
void loadWiFiCredentials();
void saveWiFiCredentials(const String& ssid, const String& password);
void handleSerialCommands();

// ===== Setup =====
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\nESP32 IoT Sensor Device - Starting...");
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize relay pins
  pinMode(FAN_PIN, OUTPUT);
  pinMode(FOG_PIN, OUTPUT);
  pinMode(LAMP_PIN, OUTPUT);
  
  // Set initial relay state (all off)
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(FOG_PIN, LOW);
  digitalWrite(LAMP_PIN, LOW);
  
  // Connect to WiFi
  loadWiFiCredentials();
  setupWiFi();
  
  // Configure MQTT
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
  
  // Set timezone for timestamp
  configTime(7 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  
  Serial.println("[SETUP] Setup complete!");
}

// ===== Main Loop =====
void loop() {
  handleSerialCommands();

  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    setupWiFi();
  }
  
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  
  mqttClient.loop();
  
  // Publish sensor data periodically
  if (millis() - lastPublish > PUBLISH_INTERVAL) {
    publishSensorData();
    lastPublish = millis();
  }
}

// ===== WiFi Setup =====
void setupWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
  
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(wifiSsid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSsid.c_str(), wifiPassword.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Failed to connect!");
  }
}

void loadWiFiCredentials() {
  preferences.begin("wifi_cfg", true);
  String savedSsid = preferences.getString("ssid", "");
  String savedPass = preferences.getString("pass", "");
  preferences.end();

  if (savedSsid.length() > 0) {
    wifiSsid = savedSsid;
    wifiPassword = savedPass;
    Serial.println("[WiFi] Loaded saved credentials from NVS");
  } else {
    wifiSsid = WIFI_SSID_DEFAULT;
    wifiPassword = WIFI_PASSWORD_DEFAULT;
    Serial.println("[WiFi] Using default credentials from firmware");
  }
}

void saveWiFiCredentials(const String& ssid, const String& password) {
  preferences.begin("wifi_cfg", false);
  preferences.putString("ssid", ssid);
  preferences.putString("pass", password);
  preferences.end();
}

void handleSerialCommands() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  // Format: WIFI:your_ssid,your_password
  if (line.startsWith("WIFI:")) {
    String payload = line.substring(5);
    int comma = payload.indexOf(',');
    if (comma <= 0) {
      Serial.println("[WiFi] Invalid format. Use WIFI:ssid,password");
      return;
    }

    String newSsid = payload.substring(0, comma);
    String newPass = payload.substring(comma + 1);
    newSsid.trim();
    newPass.trim();

    if (newSsid.length() == 0) {
      Serial.println("[WiFi] SSID must not be empty");
      return;
    }

    saveWiFiCredentials(newSsid, newPass);
    wifiSsid = newSsid;
    wifiPassword = newPass;

    Serial.println("[WiFi] Credentials saved. Reconnecting...");
    WiFi.disconnect(true, true);
    delay(300);
    setupWiFi();
    return;
  }

  if (line.equalsIgnoreCase("WIFI?")) {
    Serial.print("[WiFi] Current SSID: ");
    Serial.println(wifiSsid);
    Serial.println("[WiFi] Use WIFI:ssid,password to change");
    return;
  }

  if (line.equalsIgnoreCase("WIFI:RESET")) {
    preferences.begin("wifi_cfg", false);
    preferences.clear();
    preferences.end();
    wifiSsid = WIFI_SSID_DEFAULT;
    wifiPassword = WIFI_PASSWORD_DEFAULT;
    Serial.println("[WiFi] Saved credentials cleared. Using default.");
    WiFi.disconnect(true, true);
    delay(300);
    setupWiFi();
    return;
  }
}

// ===== MQTT Connect =====
void connectMQTT() {
  if (mqttClient.connected()) {
    return;
  }
  
  Serial.print("[MQTT] Connecting to: ");
  Serial.print(MQTT_HOST);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  
  if (mqttClient.connect(SENSOR_ID, MQTT_USER, MQTT_PASSWORD)) {
    Serial.println("[MQTT] Connected!");
    mqttClient.subscribe(MQTT_SUBSCRIBE_TOPIC);
    Serial.print("[MQTT] Subscribed to: ");
    Serial.println(MQTT_SUBSCRIBE_TOPIC);
  } else {
    Serial.print("[MQTT] Connection failed, rc=");
    Serial.println(mqttClient.state());
  }
}

// ===== Publish Sensor Data =====
void publishSensorData() {
  // Read DHT sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Check if reading is valid
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[SENSOR] Failed to read DHT sensor!");
    return;
  }
  
  // Create JSON payload
  DynamicJsonDocument doc(256);
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["sensor_id"] = SENSOR_ID;
  doc["location"] = LOCATION;
  
  // Add timestamp
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  char timestamp[25];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", timeinfo);
  doc["timestamp"] = timestamp;
  
  // Serialize to string
  String payload;
  serializeJson(doc, payload);
  
  // Publish to MQTT
  if (mqttClient.publish(MQTT_PUBLISH_TOPIC, payload.c_str())) {
    Serial.print("[PUBLISH] ");
    Serial.print("Temp: ");
    Serial.print(temperature);
    Serial.print("°C, Hum: ");
    Serial.print(humidity);
    Serial.print("% -> ");
    Serial.println(MQTT_PUBLISH_TOPIC);
  } else {
    Serial.println("[PUBLISH] Failed!");
  }
}

// ===== Handle MQTT Message =====
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Convert payload to string
  char payloadStr[length + 1];
  memcpy(payloadStr, payload, length);
  payloadStr[length] = '\0';
  
  Serial.print("[COMMAND] Received from ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payloadStr);
  
  // Parse and execute command
  parseAndExecuteCommand(payloadStr);
}

// ===== Parse and Execute Command =====
void parseAndExecuteCommand(const char* payload) {
  DynamicJsonDocument doc(384);
  DeserializationError error = deserializeJson(doc, payload);
  
  if (error) {
    Serial.print("[COMMAND] Parse error: ");
    Serial.println(error.c_str());
    return;
  }

  // Handle WiFi config payload:
  // {"wifi":{"ssid":"new_ssid","password":"new_password"}}
  JsonObject wifiObj = doc["wifi"];
  if (!wifiObj.isNull()) {
    String newSsid = wifiObj["ssid"] | "";
    String newPass = wifiObj["password"] | "";
    newSsid.trim();
    newPass.trim();

    if (newSsid.length() == 0) {
      Serial.println("[WiFi] MQTT update ignored: empty SSID");
      return;
    }

    saveWiFiCredentials(newSsid, newPass);
    wifiSsid = newSsid;
    wifiPassword = newPass;

    Serial.print("[WiFi] MQTT update saved. New SSID: ");
    Serial.println(wifiSsid);
    Serial.println("[WiFi] Reconnecting with new credentials...");

    WiFi.disconnect(true, true);
    delay(500);
    setupWiFi();
    return;
  }
  
  // Extract commands object
  JsonObject commands = doc["commands"];
  
  if (!commands) {
    // Try alternate format with serial codes
    if (doc.containsKey("serial")) {
      String serial = doc["serial"].as<String>();
      if (serial.length() >= 3) {
        // fan = serial[0], fog = serial[1], lamp = serial[2]
        setRelayState(FAN_PIN, serial[0] == '1');
        setRelayState(FOG_PIN, serial[1] == '3');
        setRelayState(LAMP_PIN, serial[2] == '5');
      }
    }
    return;
  }
  
  // Process commands
  if (commands.containsKey("fan")) {
    String fanCmd = commands["fan"].as<String>();
    setRelayState(FAN_PIN, fanCmd == "1");
  }
  
  if (commands.containsKey("fog")) {
    String fogCmd = commands["fog"].as<String>();
    setRelayState(FOG_PIN, fogCmd == "3");
  }
  
  if (commands.containsKey("lamp")) {
    String lampCmd = commands["lamp"].as<String>();
    setRelayState(LAMP_PIN, lampCmd == "5");
  }
}

// ===== Set Relay State =====
void setRelayState(int pin, bool state) {
  digitalWrite(pin, state ? HIGH : LOW);
  
  String pinName;
  if (pin == FAN_PIN) pinName = "FAN";
  else if (pin == FOG_PIN) pinName = "FOG";
  else if (pin == LAMP_PIN) pinName = "LAMP";
  
  Serial.print("[RELAY] ");
  Serial.print(pinName);
  Serial.print(" -> ");
  Serial.println(state ? "ON" : "OFF");
}
