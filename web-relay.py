#!/usr/bin/python

# To install dependencies:
#  sudo pip install Flask Flask-HTTPAuth
# sudo pip install pushbullet.py

# Configuration file 'passwd'
# Form:
# Ruben:PASSWORD:EMAIL

from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
app = Flask(__name__)
api = Api(app, prefix="/api/v1")
auth = HTTPBasicAuth()

from pushbullet import Pushbullet
import json

api_key = json.load(open("/opt/domotica/pb.json", "r"))
print "Logging in with API_KEY: "+api_key
pb = Pushbullet(api_key)

file = open("/opt/domotica/passwd", "r")
users = file.read().split("\n")
USER_DATA = {}
EMAILS = []
for user in users:
    data = user.split(":")
    if len(data) != 3:
        print "Ignoring line `"+user+"`"
        continue
    USER_DATA[data[0]] = data[1]
    EMAILS.append(data[2])

@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password

import time
import paho.mqtt.client as mqtt
mqttc=mqtt.Client()
zwaveApiReply=None
zwaveEventTopic='zwave/_EVENTS/ZWAVE_GATEWAY-zwavejs2mqtt/node/node_value_updated' 
zwaveEventReply=None
zwaveApiTopic='zwave/_CLIENTS/ZWAVE_GATEWAY-zwavejs2mqtt/api/writeValue'
def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    global zwaveApiReply
    if message.topic == zwaveApiTopic:
      zwaveApiReply = json.loads( message.payload.decode("utf-8") )
    global zwaveEventReply
    if message.topic == zwaveEventTopic:
      zwaveEventReply = json.loads( message.payload.decode("utf-8") )
def on_connect(client,userdata,flags,rc):
    mqttc.subscribe(zwaveApiTopic)
    mqttc.subscribe(zwaveEventTopic)
    print("rc: " + str(rc))
mqttc.on_message=on_message
mqttc.on_connect=on_connect
mqttc.connect("nas")
mqttc.loop_start()

import json


def sendMqttOpenDoor():
	global zwaveEventReply
	global zwaveApiReply
	zwaveEventReply = None
        zwaveApiReply = None
	print "Publishing OPEN message to MQTT..."
	mqttc.publish('zwave/_CLIENTS/ZWAVE_GATEWAY-zwavejs2mqtt/api/writeValue/set', '{ "args": [{"nodeId": 6,"commandClass": 98,"endpoint": 0,"property": "targetMode"},0]}', qos=1)
	print "Waiting for update..."
	for i in range(1,20): #wait for update
		if zwaveEventReply != None: break
		time.sleep(1)
	if zwaveApiReply == None:
		return "No reply from Zwave server! Failed..."
        if zwaveEventReply == None:
            return "No reply from Zwave lock! Zwave server replied:\n Success:"+str(zwaveApiReply[u'success'])+", "+str(zwaveApiReply[u'message'])
	lockState = zwaveEventReply['data'][1]
	prop = lockState[u'propertyName']
	prevValue = lockState[u'prevValue']
	newValue = lockState[u'newValue']
	return str(prop)+" changed from "+str(prevValue)+" to "+str(newValue)

class DoorResource(Resource):
    @auth.login_required
    def post(self):
        result = sendMqttOpenDoor()
        print "Sending notification via pushbullet"
        for email in EMAILS:
            pb.push_note("Garage", auth.username() + " opende de voordeur:\n"+result, email=email)
        return result
api.add_resource(DoorResource, '/door')

#class GarageResource(Resource):
#    @auth.login_required
#    def post(self):
#        pushButton()
#        print "Sending notification via pushbullet"
#        for email in EMAILS:
#            pb.push_note("Garage", auth.username() + " duwde op de garageknop", email=email)
#        return "Ik heb flink op de garageknop geduwd"
#
#api.add_resource(GarageResource, '/private')

#import RPi.GPIO as GPIO
#import time
#RELAY_PIN = 11 #pick a pin that is LOW by default
#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
#
#def pushButton():
#    GPIO.output(RELAY_PIN, True)
#    time.sleep(1)
#    GPIO.output(RELAY_PIN, False)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
