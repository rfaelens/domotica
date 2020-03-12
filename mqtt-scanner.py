import bluepy
import sys
import paho.mqtt.client as mqtt
import logging
from bluepy.btle import Scanner, DefaultDelegate

l = logging.getLogger()
l.setLevel(logging.DEBUG)

if len(sys.argv) != 2:
    raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint")
base = sys.argv[1]
l.info( "Scanning for LE devices to "+base )

mqttc=mqtt.Client()
mqttc.connect("nas")
mqttc.loop_start()

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        mqttc.publish(base+"/"+dev.addr, dev.rssi)
        if isNewDev:
            print("Discovered device", dev.addr, " RSSI=", dev.rssi)
        elif isNewData:
            print("Received new data from", dev.addr, " RSSI=", dev.rssi)

scanner = Scanner().withDelegate(ScanDelegate())
scanner.clear()
scanner.start()
while True:
        scanner.process(timeout=10)

scanner.stop()

devices = scanner.scan(10.0)

for dev in devices:
    print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
    for (adtype, desc, value) in dev.getScanData():
        print("  %s = %s" % (desc, value))
