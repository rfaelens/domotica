#if defined(ESP8266)
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#else
#include <WiFi.h>
#include <ESPmDNS.h>
#endif
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <Wiegand.h>
#include <PubSubClient.h>

#if defined(ESP8266)
    #define INTERRUPT_ATTR ICACHE_RAM_ATTR
#elif defined(ESP32)
  #define INTERRUPT_ATTR IRAM_ATTR
#else
    #define INTERRUPT_ATTR
#endif

/*
 * https://robertoostenveld.nl/esp-12-bootloader-modes/
 * GPIO 0, 2 and 15 determine flash state; do not use them!!
 * LED connected to GPIO16
 * 
 * D0 = GPIO16 // also BUILTIN led
 * D1 = GPIO5
 * D2 = GPIO4
 * D3 = GPIO0 // do not use
 * D4 = GPIO2 // do not use
 * 
 * D5 = GPIO14
 * D6 = GPIO12
 * D7 = GPIO13
 * D8 = GPIO15 // do not use
 * Rx = GPIO3 // also used for serial
 * Tx = GPIO1 // also used for serial
 */

// These are the pins connected to the Wiegand D0 and D1 signals.
// Ensure your board supports external Interruptions on these pins
#define PIN_D0 4 // green
#define PIN_D1 5 // white
#define PIN_GREEN_LED 14
#define PIN_BEEP 12
#define PIN_RELAY 13

#define SUBSCRIBE_TOPIC "rfid/+"

const char* ssid = "Twijglaan11";
const char* password = "jaggedwater450";
const char* mqtt_server = "192.168.10.2";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE  (256)
char msg[MSG_BUFFER_SIZE];

String clientId;

WIEGAND wg;


void callback(char* topic, byte* payload, unsigned int length) {
  String strPayload ;
  Serial.println("Received MQTT topic: ");
  Serial.println(topic);
  if (strcmp(topic, "rfid/beep") == 0) {
    digitalWrite(PIN_BEEP, false); // active low
    delay(500);
    digitalWrite(PIN_BEEP, true);
  }
  else if (strcmp(topic, "rfid/flash") == 0) {
    bool state = false;
    for(int i=0; i<8; i++) {
      digitalWrite(PIN_GREEN_LED, state);
      delay(250);
      state = !state;
    }
    digitalWrite(PIN_GREEN_LED, true); // active low
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
    digitalWrite(PIN_RELAY, false);
    detachInterrupt(PIN_D0);
    detachInterrupt(PIN_D1);
  });
  ArduinoOTA.onError([](ota_error_t error) {
    (void)error;
    ESP.restart();
  });
  ArduinoOTA.begin();
  
  pinMode(PIN_GREEN_LED, OUTPUT);
  pinMode(PIN_BEEP, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  clientId = "ESPClient-";
  clientId += String(random(0xffff), HEX);


  randomSeed(micros());
  wg.begin(PIN_D0, PIN_D1);

digitalWrite(PIN_BEEP, true);
  digitalWrite(PIN_GREEN_LED, true);
  digitalWrite(PIN_RELAY, true);
  
}


void mqttReconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    boolean success = client.connect(clientId.c_str(), "rfid/status", 0, true, "offline");
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


unsigned long last = 0;
void loop() {
  ArduinoOTA.handle();
  if (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    mqttReconnect();
  }
  client.loop();
  
  if ((millis() - last) > 10*1000) {
    client.publish("rfid/status", "online");
  }

   if (wg.available()) {
       snprintf(msg, MSG_BUFFER_SIZE, "%x", wg.getCode());
       Serial.println(msg);
       client.publish("rfid/reader", msg);
    }
}
