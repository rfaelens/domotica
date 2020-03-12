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
        raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint Mp3Filename")
MQTTEndpoint=sys.argv[1]
Mp3Filename = sys.argv[2]
l.info( "Connecting MQTT endpoint "+MQTTEndpoint+" to "+Mp3Filename )

print("Playing music...")
mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
mixer.music.load(Mp3Filename)
mixer.music.set_volume(1.0)

name = 'muziek'
def start_music(client, userdata, message):
    l.info("Received MQTT message")
    l.info("%s : %s" % (message.topic, message.payload))
    if mixer.music.get_busy():
        mixer.music.stop()
    else:
        mixer.quit()
        mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        mixer.music.load(Mp3Filename)
        mixer.music.set_volume(1.0)
        mixer.music.play()

print("Subscribing to '%s'" % (MQTTEndpoint))
subscribe.callback(start_music, MQTTEndpoint, hostname="nas")
