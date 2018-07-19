#!/usr/bin/python
import json
import sys
import time
import datetime
import paho.mqtt.client as mqtt
import Adafruit_DHT
import sys

if len(sys.argv) != 3:
    raise Exception("Usage: "+sys.argv[0]+" DHT_PIN MQTTEndpoint")
DHT_PIN=int(sys.argv[1])
base = sys.argv[2]
print( "Connecting DHT on pin "+str(DHT_PIN)+" to "+base )

DHT_TYPE = Adafruit_DHT.DHT22
FREQUENCY_SECONDS      = 30

mqttc=mqtt.Client()
mqttc.connect("nas.lan")
mqttc.loop_start()

while True:
    # Attempt to get sensor reading.
    humidity, temp = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    if humidity is None or temp is None:
        time.sleep(2)
        continue

    print('Temperature: {0:0.1f} C'.format(temp))
    print('Humidity:    {0:0.1f} %'.format(humidity))

    mqttc.publish(base+"/temp", temp)
    mqttc.publish(base+"/humidity", humidity)

    # Wait 30 seconds before continuing
    print('Published to MQTT')
    time.sleep(FREQUENCY_SECONDS)
