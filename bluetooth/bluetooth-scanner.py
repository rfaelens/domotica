#!/usr/bin/env python
from bt_rssi import BluetoothRSSI
import datetime
import time
import threading
import sys
import paho.mqtt.client as mqtt
import logging

if len(sys.argv) != 2:
    raise Exception("Usage: "+sys.argv[0]+" MQTTEndpoint")
base = sys.argv[1]

logging.basicConfig(filename='bluetooth-scanner.log',level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
l = logging.getLogger(__name__)

l.info( "Scanning for bluetooth devices to "+base )

# List of bluetooth addresses to scan
BT_ADDR_LIST = ['18:01:F1:4D:2D:38']
SLEEP = 1

mqttc=mqtt.Client()
mqttc.connect("nas")
mqttc.loop_start()

def bluetooth_listen(
        addr, sleep=1):
    b = BluetoothRSSI(addr=addr)
    while True:
        rssi = b.get_rssi()
#        l.debug("addr: {}, rssi: {}".format(addr, rssi))
        mqttc.publish(base+"/"+addr, rssi)
        # Delay between iterations
        time.sleep(sleep)


def start_thread(addr, sleep=SLEEP):
    thread = threading.Thread(
        target=bluetooth_listen,
        args=(),
        kwargs={
            'addr': addr,
            'sleep': sleep
        }
    )
    # Daemonize
    thread.daemon = True
    # Start the thread
    thread.start()
    return thread


def main():
    threads = []
    for addr in BT_ADDR_LIST:
        th = start_thread(addr=addr)
        threads.append(th)
    while True:
        # Keep main thread alive
        time.sleep(1)

if __name__ == '__main__':
    main()
