#if defined(ARDUINO_ESP8266)
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#endif

#if defined(ARDUINO_ESP32)
#include <WiFi.h>
#include <ESPmDNS.h>
#endif

#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#define MQTT_MAX_PACKET_SIZE 2048
#include <PubSubClient.h>





const char* ssid = "Twijglaan11";
const char* password = "XXXXXXXXTODOXX";
const char* mqtt_server = "192.168.10.2";


WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
// See https://pubsubclient.knolleary.net/api#getBufferSize
#define MSG_BUFFER_SIZE  (256)
char msg[MSG_BUFFER_SIZE];
int value = 0;

#define BUILTIN_LED 2
#define IR_ANALOG A0

int readings [512];
int maxRead = 128;
int readIndex  = 0;
long total  = 0;

#define SUBSCRIBE_TOPIC "watermeter/+"

int sampleDelay = 2000; // in us
int sendInterval = 500; // in ms
double consumption = 0.0;
#define CONSUMPTION_PER_PULSE 0.5
bool lastState = false;
int upThreshold = 36;
int downThreshold = 32;


void callback(char* topic, byte* payload, unsigned int length) {
  String strPayload ;
  if (strcmp(topic,"watermeter/sampleDelay")==0) {
    strPayload = String((char*)payload);
    sampleDelay = strPayload.toInt();
  }
  if (strcmp(topic,"watermeter/sendInterval")==0) {
    strPayload = String((char*)payload);
    sendInterval = strPayload.toInt();
  }
  if (strcmp(topic,"watermeter/upThreshold")==0) {
    strPayload = String((char*)payload);
    upThreshold = strPayload.toInt();
  }
  if (strcmp(topic,"watermeter/downThreshold")==0) {
    strPayload = String((char*)payload);
    downThreshold = strPayload.toInt();
  }
  if (strcmp(topic,"watermeter/consumption")==0) {
    strPayload = String((char*)payload);
    consumption = strPayload.toDouble();
  }
}

String clientId;

void setup() {
  pinMode(BUILTIN_LED, OUTPUT);
  randomSeed(micros());
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  Serial.begin(115200);
  Serial.println("Booting");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  ArduinoOTA.begin();

  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  String randomId = String(random(0xffff), HEX);
  clientId = "ESPClient-"+randomId;
}

void publishConfig() {
  client.publish("watermeter/status", "online", true);
  snprintf(msg, MSG_BUFFER_SIZE, "{\"rssi\":%d,\"bssid\":\"%s\",\"maxRead\":%d,\"sendInterval\":%d,\"sampleDelay\":%d,\"avgTime\":%d}", 
    WiFi.RSSI(), 
    WiFi.BSSIDstr().c_str(),
    maxRead,
    sendInterval,
    sampleDelay,
    sampleDelay * maxRead / 1000
  );
  client.publish("watermeter/config", msg);

  client.publish("homeassistant/number/watermeter/config",
    "{\"~\":\"watermeter/consumption\",\"stat_t\":\"~\",\"cmd_t\":\"~\",\"max\":999999,\"name\":\"Watermeter Consumption\",\"avty_t\":\"watermeter/status\",\"icon\":\"mdi:water-pump\",\"ret\":true,\"step\":0.5}",
    true
  );
}

void mqttReconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    boolean success = client.connect(clientId.c_str(), "watermeter/status", 0, true, "offline");
    if (success) {
      //Serial.println("connected");
      publishConfig();
      client.subscribe(SUBSCRIBE_TOPIC);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(500);
    }
  }
}

void pulseUp() {
  pulse();
  digitalWrite(BUILTIN_LED, true);
}
void pulseDown() {
  pulse();
  digitalWrite(BUILTIN_LED, false);
}

void pulse() {
  consumption = consumption + CONSUMPTION_PER_PULSE;
  snprintf (msg, 12, "%lf", consumption);
  client.publish("watermeter/consumption", msg, true);
}

void loop() {
  ArduinoOTA.handle();  
  if (!client.connected()) {
    mqttReconnect();
  }
  client.loop();
  
  delayMicroseconds(sampleDelay);
  int a;
  a=analogRead(IR_ANALOG);
  
  total = total - readings[readIndex];
  readings[readIndex] = a;
  total = total + readings[readIndex];
  readIndex = readIndex + 1;
  if (readIndex >= maxRead) {
    readIndex = 0;
  }
  long avg = total / maxRead;

  if(lastState == false && avg > upThreshold) {
    pulseUp();
    lastState = true;
  } else if (lastState == true && avg < downThreshold) {
    pulseDown();
    lastState = false;
  }

  unsigned long now = millis();
  if (now - lastMsg > sendInterval) {
    lastMsg = now;
    snprintf (msg, 3, "%d", a);
    client.publish("watermeter/analog", msg);
    snprintf (msg, 3, "%d", avg);
    client.publish("watermeter/avg", msg);
  }
}
