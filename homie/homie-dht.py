#!/usr/bin/python
from homie.device_temperature_humidity import Device_Temperature_Humidity
import json
import sys
import datetime
import Adafruit_DHT
import sys
import logging
import time


import homieconnect
mqtt_settings = homieconnect.mqtt_settings


if len(sys.argv) != 3:
    raise Exception("Usage: "+sys.argv[0]+" DHT_PIN device_id")
DHT_PIN=int(sys.argv[1])
device_id = sys.argv[2]
logging.basicConfig(filename=device_id+'.log',level=logging.DEBUG)
l = logging.getLogger(__name__)
l.info( "Connecting DHT on pin "+str(DHT_PIN)+" to "+device_id )

DHT_TYPE = Adafruit_DHT.DHT22
FREQUENCY_SECONDS      = 10


## Store the last X temperatures in a list
HP_LEN = 4
HP_CUT = 4 #if more then 4 deg difference from the mean, ignore signal
stack = []

temp_hum = Device_Temperature_Humidity(device_id=device_id, name=device_id, homie_settings={}, mqtt_settings=mqtt_settings, temp_units="C")

while True:
    l.debug("Reading DHT sensor...")
    # Attempt to get sensor reading.
    humidity, temp = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    if humidity is None or temp is None:
        l.debug("Read error, retrying in 2")
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

    temp_hum.update_temperature(temp)
    temp_hum.update_humidity(humidity)

    # Wait a while before continuing
    l.debug('Published to MQTT')
    time.sleep(FREQUENCY_SECONDS)
