#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import json
import sys
import time
import datetime
import paho.mqtt.client as mqtt
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
    raise Exception("Usage: "+sys.argv[0]+" SWITCH_PIN MQTTEndpoint")
SW_PIN=int(sys.argv[1])
base = sys.argv[2]
l.info( "Connecting switch on pin "+str(SW_PIN)+" to "+base )

mqttc=mqtt.Client()
mqttc.connect("nas")
mqttc.loop_start()

# handle the button event
def buttonEventHandler (pin):
    mqttc.publish(base+"/button", True)
    l.info("Button pressed")
GPIO.setmode(GPIO.BCM)
GPIO.setup(SW_PIN,GPIO.IN)
GPIO.add_event_detect(SW_PIN,GPIO.FALLING, callback=buttonEventHandler, bouncetime=500)

while True:
    time.sleep(1)
