#!/usr/bin/python3.5
from eq3bt import Thermostat
import paho.mqtt.client as mqtt
import time
import sys

if len(sys.argv) != 3:
    raise Exception("Usage: "+sys.argv[0]+" MAC MQTTEndpoint")

btmac=sys.argv[1]
base = sys.argv[2]
print( "Connecting eq3bt "+btmac+" to "+base )

thermostat = Thermostat(btmac)
mqttc=mqtt.Client()
mqttc.connect("nas.lan")
mqttc.loop_start()

while True:
	try:
		thermostat.update()
	except Exception as e:
		print(e)
		print("Error connecting to thermostat; trying again")
		continue
	print(thermostat)
	mqttc.publish(base+"/target", thermostat.target_temperature) #target
	mqttc.publish(base+"/mode", thermostat.mode_readable) #mode
	mqttc.publish(base+"/valve_state", thermostat.valve_state) #valve_state
	mqttc.publish(base+"/window_open", thermostat.window_open) #window_open
	mqttc.publish(base+"/locked", thermostat.locked) #
	mqttc.publish(base+"/low_battery", thermostat.low_battery) #
	mqttc.publish(base+"/min_temp", thermostat.min_temp) #
	mqttc.publish(base+"/max_temp", thermostat.max_temp) #
	mqttc.publish(base+"/away_end", str(thermostat.away_end)) #
	mqttc.publish(base+"/boost", thermostat.boost) #in boost mode?
	# TODO: schedules?
	time.sleep(300)
