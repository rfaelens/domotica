import time
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt


from pygame import mixer  # Load the popular external library
import time
import RPi.GPIO as GPIO
import json
import sys
import time
import datetime
import os
import paho.mqtt.client as mqtt
import sys
import logging

import pygame

#logging.basicConfig(format='%(asctime)s %(message)s')
l = logging.getLogger()
l.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
l.addHandler(ch)

if len(sys.argv) != 3:
        raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint Mp3Filename")
MQTTEndpoint=sys.argv[1]
Mp3Filename = sys.argv[2]
l.info( "Connecting MQTT endpoint "+MQTTEndpoint+" to "+Mp3Filename )


print("Initializing GPIO pin")
RELAY_PIN = 3

GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)



print("Playing music...")
mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
mixer.music.load(Mp3Filename)
mixer.music.set_volume(1.0)

mixer.music.set_endevent(pygame.constants.USEREVENT)
#os.environ['SDL_AUDIODRIVER'] = 'dsp'

name = 'deurbel'
def start_music(client, userdata, message):
    l.info("Received MQTT message")
    l.info("%s : %s" % (message.topic, message.payload))
    GPIO.output(RELAY_PIN, True)
    if mixer.music.get_busy():
        mixer.music.stop()
    else:
        mixer.quit()
        mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        mixer.music.load(Mp3Filename)
        mixer.music.set_volume(1.0)
        mixer.music.play()

print("Set up endEvent listener")

os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()

# Code to execute in an independent thread
import time
def check_is_stop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.constants.USEREVENT:
              print("EndEvent found!")
              GPIO.output(RELAY_PIN, False)
        time.sleep(1)
# Create and launch a thread
from threading import Thread
t = Thread(target = check_is_stop, args =())
t.start()

print("Subscribing to '%s'" % (MQTTEndpoint))


while True:
    print("Trying to connect...")
    subscribe.callback(start_music, MQTTEndpoint, hostname="nas")
    time.sleep(1)
