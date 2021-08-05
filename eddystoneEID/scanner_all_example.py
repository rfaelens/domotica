import time
from beacontools import BeaconScanner, IBeaconFilter
import eidtools
import math
import sys
import logging
import paho.mqtt.client as mqtt

KEYS = {
        'ruben': {'ik':bytes.fromhex("43ed0a8604b61774123c2cd01d125c6c"), 'scaler':9}
        }

if len(sys.argv) != 2:
    raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint")
MQTTEndpoint=sys.argv[1]

logging.basicConfig(filename='beacontools.log',level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
#logging.basicConfig(format=FORMAT,level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
l = logging.getLogger(__name__)
l.info( "Detecting EDID presence and publishing to "+MQTTEndpoint )

mqttc=mqtt.Client()
mqttc.connect("nas")
mqttc.loop_start()

def presence_detected(k, tx_power, rssi):
    n=1.5    #Path loss exponent(n) = 1.5
    c = 10   #Environment constant(C) = 10
    A0 = tx_power   #Average RSSI value at d0=1m
    x = float((rssi-A0)/(-10*n))         #Log Normal Shadowing Model considering d0 =1m where
    distance = (math.pow(10,x) * 100) + c
    mqttc.publish(MQTTEndpoint+"/"+k+"/rssi", rssi)
    mqttc.publish(MQTTEndpoint+"/"+k+"/distance", distance)
#    print("Presence detected at d=" + str(distance))
                             

def callback(bt_addr, rssi, packet, additional_info):
#    print("<%s, %d> %s %s" % (bt_addr, rssi, packet, additional_info))
    eid = packet.eid
    for k, v in KEYS.items():
        ik  =v['ik']
        scaler = v['scaler']
        beacon_time_seconds = int(time.time())
        eid = eidtools.GetAndPrintEid(ik, scaler, beacon_time_seconds)
        if packet.eid == eid:
#            print("Detected "+k+" presence (auth succesful)")
            presence_detected(k, packet.tx_power, rssi) 

# scan for all iBeacon advertisements from beacons with the specified uuid 
scanner = BeaconScanner(callback)
scanner.start()
time.sleep(180)
scanner.stop()
