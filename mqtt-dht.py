#!/usr/bin/python
import json
import sys
import time
import datetime
import paho.mqtt.client as mqtt
import Adafruit_DHT
import sys
import logging

#logging.basicConfig(format='%(asctime)s %(message)s')
l = logging.getLogger()
l.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
l.addHandler(ch)

if len(sys.argv) != 3:
    raise Exception("Usage: "+sys.argv[0]+" DHT_PIN MQTTEndpoint")
DHT_PIN=int(sys.argv[1])
base = sys.argv[2]
l.info( "Connecting DHT on pin "+str(DHT_PIN)+" to "+base )

DHT_TYPE = Adafruit_DHT.DHT22
FREQUENCY_SECONDS      = 30

mqttc=mqtt.Client()
mqttc.connect("nas.lan")
mqttc.loop_start()

## Store the last X temperatures in a list
HP_LEN = 4
HP_CUT = 4 #if more then 4 deg difference from the mean, ignore signal
stack = []

while True:
    # Attempt to get sensor reading.
    humidity, temp = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    if humidity is None or temp is None:
        time.sleep(2)
        continue

    l.debug('Temperature: {0:0.1f} C'.format(temp))
    l.debug('Humidity:    {0:0.1f} %'.format(humidity))

    stack.insert(0, temp)
    if len(stack) > HP_LEN:
        stack.pop()
        mean = sum(stack) / len(stack)
        l.debug('AVGtemp:    {0:0.1f} C'.format(mean))
        if abs(temp - mean) > HP_CUT:
            l.warn('Temp {0:0.1f} too different from rolling mean {0:0.1f}, not relaying to MQTT')
            continue
        else:
            l.debug('Temp within limits of rolling mean, OK')

    mqttc.publish(base+"/temp", temp)
    mqttc.publish(base+"/humidity", humidity)

    # Wait a while before continuing
    l.debug('Published to MQTT')
    time.sleep(FREQUENCY_SECONDS)
