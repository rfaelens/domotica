#!/usr/bin/python

# To install dependencies:
#  sudo pip install Flask Flask-HTTPAuth

from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
app = Flask(__name__)
api = Api(app, prefix="/api/v1")
auth = HTTPBasicAuth()

file = open("passwd", "r")
users = file.read().split("\n")
USER_DATA = {}
for user in users:
    data = user.split(":")
    if len(data) != 2:
        print "Ignoring line `"+user+"`"
        continue
    USER_DATA[data[0]] = data[1]

@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password

class PrivateResource(Resource):
    @auth.login_required
    def get(self):
        return {"meaning_of_life": 42}
    def post(self):
        pushButton()
        return "Ik heb flink op de garageknop geduwd"

api.add_resource(PrivateResource, '/private')

import RPi.GPIO as GPIO
import time
RELAY_PIN = 11 #pick a pin that is LOW by default
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

def pushButton():
    GPIO.output(RELAY_PIN, True)
    time.sleep(1)
    GPIO.output(RELAY_PIN, False)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
