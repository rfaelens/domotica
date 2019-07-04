import RPi.GPIO as GPIO
import time
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt

name = 'boiler-relay'
RELAY_PIN = 5

GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

def toBool(payload):
    msg = payload.decode("utf-8").lower()
    if msg == "on":
        return True
    if msg == "true":
        return True
    if msg == "1":
        return True
    return False

def set_relay(client, userdata, message):
    print("%s : %s" % (message.topic, message.payload))
    GPIO.output(RELAY_PIN, toBool(message.payload))

print("Subscribing to %s" % ("boiler/set"))
subscribe.callback(set_relay, "boiler/set", hostname="nas.lan")
