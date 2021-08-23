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


if len(sys.argv) != 4:
        raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint iopin Mp3Dir")
MQTTEndpoint=sys.argv[1]
iopin = int(sys.argv[2])
Mp3Dir = sys.argv[3]
Mp3Filename = Mp3Dir ## TODO: add directory options
logging.basicConfig(filename='player.log',level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
l = logging.getLogger(__name__)
l.info( "Connecting MQTT endpoint "+MQTTEndpoint+" to "+Mp3Dir+" (playButton on pin="+str(iopin)+")" )

mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
mixer.music.load(Mp3Filename)
mixer.music.set_volume(1.0)

## First start the music thread
## It listens to the button and plays music
def playStop():
    if mixer.music.get_busy():
        mixer.music.stop()
    else:
        mixer.quit()
        mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        mixer.music.load(Mp3Filename)
        mixer.music.set_volume(1.0)
        mixer.music.play()

def buttonEventHandler (pin):
    playStop()
GPIO.setmode(GPIO.BCM)
GPIO.setup(iopin,GPIO.IN)
GPIO.add_event_detect(iopin,GPIO.FALLING, callback=buttonEventHandler, bouncetime=500)

def start_music(client, userdata, message):
    l.info("Pressing Play/Stop")
    playStop()

while True:
    try:
        print("Subscribing to '%s'" % (MQTTEndpoint))
        subscribe.callback(start_music, MQTTEndpoint, hostname="nas")
    except:
        l.warn("Error subscribing, retrying...")
        time.sleep(10)
