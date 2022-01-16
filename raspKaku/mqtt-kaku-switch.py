#!/usr/bin/python

# Author: Ruben Faelens, (C) 2021
# Goal: Transmit Klik-Aan-Klik-Uit protocol in python
# Based on NewRemoteSwitch library v1.1.0 by Randy Simons http://randysimons.nl
# GPLv3
import sys
print("Starting...")

if len(sys.argv) != 2:
    raise Exception("Usage: "+sys.argv[0]+" device1-device2-device3")
devices = sys.argv[1].split("-")
devices = list( map(int, devices) )
print( "Connecting kaku endpoints "+sys.argv[1])

import paho.mqtt.client as mqtt
import os
import time
import pigpio
import regex
import kaku
print("Connecting to <nas>")
mqttc=mqtt.Client()

pin = 8 ## wiringPi pin 10, BCM pin 8
print("Sending waveform on pin "+str(pin))
pi = pigpio.pi()
pi.set_mode(pin, pigpio.OUTPUT)

address = "M"
period = 375 #375 us

print("Registering waveforms with pigpio")
pi.wave_clear()
waveCodes = {}
for device in devices:
    print("for device "+str(device))
    wave = kaku.buildWave(kaku.buildFrame(address, device, False),
            period, pin)
    pi.wave_add_generic(wave)
    codeOff = pi.wave_create()
    wave = kaku.buildWave(kaku.buildFrame(address, device, True),
            period, pin)
    pi.wave_add_generic(wave)
    codeOn = pi.wave_create()
    waveCodes[device] = [codeOff, codeOn]
print("registration complete")

import regex
def on_message(client, userdata, message):
    print("Received message '" + str(message.payload) + "' on topic '"
        + message.topic + "' with QoS " + str(message.qos))
    
    m = regex.compile('kaku/M_(\\d+)/set').match(message.topic)
    device=int(m.group(1))
    
    if message.payload == b"ON":
        value = 1
    elif message.payload == b"OFF":
        value = 0
    else:
        print("WARNING: unknown payload "+str(message.payload)+", use ON or OFF")
        return()
    
    wave_id = waveCodes[device][value]
    pi.wave_send_repeat(wave_id)
    time.sleep(0.2)
    pi.wave_tx_stop() # stop waveform
    
    #print("publishing state...")
    mqttc.publish("kaku/M_"+str(device)+"/state", message.payload)


#mqttc.publish("homeassistant/switch/livingsfeer_kaku/config", '{"~":"'+topic+'", "name":"livingsfeer_kaku", "command_topic":"~/set", "state_topic":"~/state"}')
def on_connect(client, userdata, flags, rc):
    print('Advertising presence for '+str(devices))
    for device in devices:
        device = str(device)
        topic='kaku/M_'+device
        print("advertising "+device+" at "+topic)
        mqttc.publish("homeassistant/switch/living_kaku_"+device+"/config", '{"~":"'+topic+'", "name":"living_kaku_'+device+'", "unique_id": "living_kaku_'+device+'", "command_topic":"~/set"}', retain=True)
        mqttc.subscribe(topic+"/set")
    print("done")

print("Registering MQTTC callbacks")
mqttc.on_message = on_message
mqttc.on_connect = on_connect

print("Loop forever...")
#mqttc.loop_forever()
mqttc.connect("nas")
mqttc.loop_forever(retry_first_connection=True)
