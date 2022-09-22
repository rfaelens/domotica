#include <ESPiLight.h>

#if defined(ESP8266)
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#else
#include <WiFi.h>
#include <ESPmDNS.h>
#endif
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <PubSubClient.h>


#define RECEIVER_PIN 4
#define BUILTIN_LED 2
#define ADDRESS 'M'
#define DEVICE 12
#define TRANSMITTER_PIN 15

#define SUBSCRIBE_TOPIC "kaku/#"

const char* ssid = "XXXX";
const char* password = "YYYY";
const char* mqtt_server = "192.168.10.2";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE  (256)
char msg[MSG_BUFFER_SIZE];


String clientId;

ESPiLight rf(TRANSMITTER_PIN);  // use -1 to disable transmitter

bool startsWith(const char *str, const char *start) {
    return strncmp(start, str, strlen(start)) == 0;
}

bool endsWith(const char *str, const char *end) {
  int n = strlen(str);
  int m = strlen(end);
  return strcmp(str+n-m, end) == 0;
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("Received MQTT topic: ");
  Serial.println(topic);
  Serial.println("Payload:");
  Serial.println((char*)payload);
  int unit = topic[5] - 65;
  int id = atoi(topic+7) - 1; // strtol keeps going until the first non-int character
  if (endsWith(topic, "set")) {
    bool isOn = strncmp((char*)payload, "ON", length) == 0;
    bool isOff = strncmp((char*)payload, "OFF", length) == 0;
    Serial.print("ON? "); Serial.println(isOn);
    Serial.print("OFF? "); Serial.println(isOff);
    if(isOn) {
      snprintf(msg, MSG_BUFFER_SIZE, "{\"id\":%d,\"unit\":%d,\"on\":1}", id, unit); // the value of "on" does not matter
    } else {
      snprintf(msg, MSG_BUFFER_SIZE, "{\"id\":%d,\"unit\":%d,\"off\":1}", id, unit);
    }
    rf.send("arctech_switch_old", msg);
    Serial.println(msg);
  }
}

void rfCallback(const String &protocol, const String &message, int status,
                size_t repeats, const String &deviceID) {
  Serial.print("RF signal arrived [");
  Serial.print(protocol);  // protocoll used to parse
  Serial.print("][");
  Serial.print(deviceID);  // value of id key in json message
  Serial.print("] (");
  Serial.print(status);  // status of message, depending on repeat, either:
                         // FIRST   - first message of this protocoll within the
                         //           last 0.5 s
                         // INVALID - message repeat is not equal to the
                         //           previous message
                         // VALID   - message is equal to the previous message
                         // KNOWN   - repeat of a already valid message
  Serial.print(") ");
  Serial.print(message);  // message in json format
  Serial.println();

  // check if message is valid and process it
  if (status == VALID) {
    Serial.print("Valid message: [");
    Serial.print(protocol);
    Serial.print("] ");
    Serial.print(message);
    Serial.println();
    client.publish("kaku/receive", message.c_str());
  }
}

void setup() {
  Serial.begin(115200);

Serial.println("Starting up...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println("Connected to WIFI");

  ArduinoOTA
  .onStart([]() {
    
  });
  ArduinoOTA.onError([](ota_error_t error) {
    (void)error;
    ESP.restart();
  });
  ArduinoOTA.begin();
  
  // set callback funktion
  rf.setCallback(rfCallback);
  // inittilize receiver
  rf.initReceiver(RECEIVER_PIN);
  
  randomSeed(micros());
  clientId = "ESPClient-";
  clientId += String(random(0xffff), HEX);
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void mqttReconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    boolean success = client.connect(clientId.c_str(), "kaku/status", 0, true, "offline");
    if (success) {
      client.subscribe(SUBSCRIBE_TOPIC);
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(100);
    }
  }
}

long last = 0;
void loop() {
  ArduinoOTA.handle();
  if (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    mqttReconnect();
  }
  client.loop();
  rf.loop();
  delay(10);
  if(millis() > last + 2000) {
    last=millis();
    client.publish("kaku/status", "online");
  }
}
