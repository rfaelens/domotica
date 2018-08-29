#from bluepy.btle import Scanner, DefaultDelegate
import paho.mqtt.client as mqtt
import time
import sys
import bluepy.btle as btle
from datetime import datetime

address="54:4a:16:2f:ab:0b"
if len(sys.argv) != 3:
    raise Exception("Usage: mqtt-btscanner.py Address Base")

address = sys.argv[1]
base = sys.argv[2]


mqttc=mqtt.Client()

# example:
#dc00010205030000000101
#dc00010205030000010101
#dc00010205030000020101
#dc00010205030000030101
#dc00010205030000040101
#dc00010205030000050101
#dc00010205030000060101
#dc00010205020000060101
#dc00010205030000060101
#dc00010205030000070101
#dc00010205030000080101
#dc00010205030000090101
#dc00010205030000090501
#dc000102050300000a0501
#dc000102050300000b0501
#dc000102050300000c0201
#dc000102050300000d0201
#dc000102050300000e0201
#dc000102050300000e0401
#dc000102050300000f0401
#dc00010205030000100401
#dc00010205030000100301
#dc00010205030000110301
#dc00010205030000120301
#dc00010205020000120301
# dc 00 01 02 05 03 c0 00 09 01 01
# dc:00:01:02:05:02:00:00:12:03:01


class ScanDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr <> address: return
        
#        message = dev.addr+' '
#        if isNewDev: message+='NEW'
#        if isNewData: message+='UPDATE'
#        message += "  (RSSI="+str(dev.rssi)+",updateCount="+str(dev.updateCount)+")"
#        print message
        if isNewDev or isNewData:
            bytes=dev.getValueText(255).decode('hex')
            mqttc.publish(base+"/running", ord(bytes[5]) )
            mqttc.publish(base+"/pressure", ord(bytes[6]) )
            mqttc.publish(base+"/time", ord(bytes[8]) )
            mqttc.publish(base+"/mode", ord(bytes[9]) )

            for adtype, description, value in dev.getScanData():
                print dev.addr+": [adtype='"+str(adtype)+"',descr='"+description+"',value='"+value+"'"

mqttc.connect("nas.lan")
mqttc.loop_start()

scanner = btle.Scanner().withDelegate(ScanDelegate())
scanner.start(passive=True)
while True:
#        print "Still running..."
        try:
            scanner.process()
        except btle.BTLEException as e:
            print('Problem with the Bluetooth adapter : {}'.format(e))
            print('Retrying...')
