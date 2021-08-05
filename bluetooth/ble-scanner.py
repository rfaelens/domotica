import bluepy
import sys
import paho.mqtt.client as mqtt
import logging
from bluepy.btle import Scanner, DefaultDelegate

if len(sys.argv) != 2:
    raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint")
base = sys.argv[1]

logging.basicConfig(filename='mqtt-scanner.log',level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
l = logging.getLogger(__name__)

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
            l.info("Discovered device %s RSSI=%s" % (dev.addr,dev.rssi) )
        elif isNewData:
            l.info("Received new data from %s RSSI=%s" % (dev.addr,dev.rssi) )
        else:
            l.info("Not newDev of newData for %s RSSI=%s" % (dev.addr, dev.rssi) )
    def handleNotification(cHandle, data):
        l.info("Received notification from %s" % (cHandle))

scanner = Scanner().withDelegate(ScanDelegate())
#scanner.clear()
#scanner.start()
while True:
        time.sleep(5) #10 seconds
        l.info("Processing scan...")
        try:
            scanner.scan(2) #2 seconds scan
        except bluepy.btle.BTLEManagementError as e:
            l.debug("Error, retry...")
        except bluepy.btle.BTLEDisconnectError as e:
            l.debug("Error, retry...")
#        scanner.process(timeout=10)

#scanner.stop()
