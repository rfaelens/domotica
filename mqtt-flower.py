#!/usr/bin/python3.5
from miflora.miflora_poller import MiFloraPoller
from btlewrap import BluepyBackend
import paho.mqtt.client as mqtt
import time
import sys

if len(sys.argv) != 3:
    raise Exception("Usage: mqtt-flower.py MAC MQTTEndpoint")

btmac=sys.argv[1]
base = sys.argv[2]
print( "Connecting flower "+btmac+" to "+base )
p = MiFloraPoller(btmac, BluepyBackend)


mqttc=mqtt.Client()
mqttc.connect("nas.lan")
mqttc.loop_start()

while True:
	try:
		p.fill_cache()
	except Exception as e:
		print(e)
		print("Error connecting to Mii flower care; trying again")
		continue
	print(p.name())
	print(p.parameter_value("temperature"))
	print(p.parameter_value("light"))
	print(p.parameter_value("moisture"))
	mqttc.publish(base+"/firmware", p.firmware_version())
	mqttc.publish(base+"/name", p.name())
	for i in ("temperature", "light", "moisture", "conductivity", "battery"):
		mqttc.publish(base+"/"+i, p.parameter_value(i))
	time.sleep(300)
