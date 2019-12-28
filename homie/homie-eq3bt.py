#!/usr/bin/env python
from homie.device_base import Device_Base
from homie.node.node_contact import Node_Contact
from homie.node.property.property_contact import Property_Contact
from homie.node.property.property_temperature import Property_Temperature
from homie.node.node_base import Node_Base
import logging
from eq3bt import Thermostat
import eq3bt
import sys
import time

logger = logging.getLogger(__name__)
eq3bt.connection.DEFAULT_TIMEOUT=100
logging.basicConfig(level=logging.DEBUG)

if len(sys.argv) != 3:
    raise Exception("Usage: "+sys.argv[0]+" MAC DeviceID")
btmac=sys.argv[1]
device_id = sys.argv[2]
logger.debug( "Connecting eq3bt "+btmac+" to "+device_id )

thermostat = Thermostat(btmac)
mqtt_settings = {
    'MQTT_BROKER' : 'nas',
    'MQTT_PORT' : 1883,
}

class Node_EQ3BT(Node_Base):
    def __init__(self, device, id='contact', name='EQ3BT', type_='eq3bt', retain=True, qos=1): 
        super().__init__(device,id,name,type_,retain,qos)
        self.add_property(Property_Temperature(self,id='target',name='Target',settable=True,unit='C', set_value=self.set_target) )
#        self.add_property(Property_Mode())
    def update_state(self,thermostat):
        self.get_property('target').value = thermostat.target_temperature
        #mqttc.publish(base+"/target", thermostat.target_temperature) #target; Float in Celcius
        #mqttc.publish(base+"/mode", thermostat.mode_readable) #string; "auto dst"
        #mqttc.publish(base+"/valve_state", thermostat.valve_state) #valve_state; integer between 0-100
        #mqttc.publish(base+"/window_open", thermostat.window_open) #window_open; Boolean
        #mqttc.publish(base+"/locked", thermostat.locked) #Boolean
        #mqttc.publish(base+"/low_battery", thermostat.low_battery) #Boolean
        #mqttc.publish(base+"/min_temp", thermostat.min_temp) #Float in Celcius
        #mqttc.publish(base+"/max_temp", thermostat.max_temp) #Float in Celcius
        #mqttc.publish(base+"/away_end", str(thermostat.away_end)) #either None (NULL) or ??
        #mqttc.publish(base+"/boost", thermostat.boost) #in boost mode? Boolean
        #mqttc.publish(base+"/firmware_version", thermostat.firmware_version)
        #mqttc.publish(base+"/device_serial", thermostat.device_serial)
    def set_target(self,x):
        thermostat.target_temperature=x

class Device_EQ3BT(Device_Base):
    def __init__(self, device_id=None, name=None, homie_settings=None, mqtt_settings=None):
        super().__init__ (device_id, name, homie_settings, mqtt_settings)
        self.add_node(Node_EQ3BT(self,id='eq3bt'))
        self.start()
    def update(self,thermostat):
        self.get_node('eq3bt').update_state(thermostat)


homie = Device_EQ3BT(device_id='bla', name='Test EQ3BT', mqtt_settings=mqtt_settings)

while True:
        try:
            thermostat.update()
        except Exception as e:
            print(e)
            print("Error connecting to thermostat; trying again")
            continue
        if thermostat._raw_mode == None:
            print("No reply received from thermostat... Strange!")
            time.sleep(300)
            continue #no message received within acceptable time...
        print(thermostat)
        homie.update(thermostat)
        time.sleep(300)
