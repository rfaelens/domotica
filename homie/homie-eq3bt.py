#!/usr/bin/env python
import re
from homie.device_base import Device_Base
from homie.node.node_contact import Node_Contact
from homie.node.property.property_contact import Property_Contact
from homie.node.property.property_temperature import Property_Temperature
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_enum import Property_Enum
from homie.node.property.property_string import Property_String
from homie.node.node_base import Node_Base
import homie
import logging
from eq3bt import Thermostat
import eq3bt
import sys
import time
from homie.mqtt.paho_mqtt_client import PAHO_MQTT_Client
from paho.mqtt.client import Client

eq3bt.connection.DEFAULT_TIMEOUT=500

if len(sys.argv) < 3:
    raise Exception("Usage: "+sys.argv[0]+" MAC DeviceID [DeviceName]")
btmac=sys.argv[1]
device_id = sys.argv[2]
if len(sys.argv) == 3:
    device_name = device_id
else:
    device_name = sys.argv[3]

logging.basicConfig(filename=device_id+'.log',level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
l = logging.getLogger(__name__)
l.debug( "Connecting eq3bt "+btmac+" to "+device_id )

thermostat = Thermostat(btmac)

import homieconnect
mqtt_settings = homieconnect.mqtt_settings

import homie.node.property.property_boolean as property_boolean
#from homie.node.property.property_boolean import Property_Boolean
class Property_Boolean(property_boolean.Property_Boolean):
    @property_boolean.Property_Boolean.value.setter
    def value(self, value, retain=True, qos=1):
         if value:
            str_value="true"
         else:
            str_value="false"
         property_boolean.Property_Boolean.value.fset(self, value=str_value, retain=retain, qos=qos)
class Node_EQ3BT(Node_Base):
    def __init__(self, device, id='eq3bt', name='EQ3BT', type_='eq3bt', retain=True, qos=1): 
        super().__init__(device,id,name,type_,retain,qos)
        self.add_property(Property_Temperature(self,id='target-temperature',name='Target temperature',unit='C', set_value=self.set_target_temperature, settable=True) )
        self.add_property(Property_Integer(self, id="valve-state", name="Valve state", settable=False, unit="%", data_format="0:100"))
        self.add_property(Property_Boolean(self, id="low-battery", name="Low battery", settable=False))
        self.add_property(Property_Enum(self, id="mode", name="Mode", data_format="Boost,Away,Closed,Open,Manual,Auto", settable=True, set_value=self.set_mode))
        self.add_property(Property_Boolean(self, id="mode-manual", name="Mode manual", settable=True, set_value=self.set_mode_manual))
        self.add_property(Property_Boolean(self, id="mode-away", name="Mode away", settable=False))
        self.add_property(Property_Boolean(self, id="mode-dst", name="Mode dst", settable=False))
        self.add_property(Property_Boolean(self, id="mode-window", name="Mode window", settable=False))
        self.add_property(Property_Boolean(self, id="locked", name="Locked", set_value=self.set_locked, settable=True))
        self.add_property(Property_Boolean(self, id="boost", name="Boost", set_value=self.set_boost, settable=True))
        self.add_property(Property_Temperature(self,id='comfort-temperature',name='Comfort temperature',unit='C', settable=False) )
        self.add_property(Property_Temperature(self,id='eco-temperature',name='Eco temperature',unit='C', settable=False) )
        self.add_property(Property_Temperature(self,id='temperature-offset',name='Temperature offset',settable=True,unit='C', set_value=self.set_temperature_offset) )
        self.add_property(Property_Temperature(self,id='min-temp',name='Minimum temperature',unit='C', settable=False) )
        self.add_property(Property_Temperature(self,id='max-temp',name='Maximum temperature',unit='C', settable=False) )
        self.add_property(Property_String(self, id="firmware-version", name="Firmware version", settable=False))
        self.add_property(Property_String(self, id="device-serial", name="Device serial", settable=False))
        #no AWAY mode yet; too complex
        # no window Open config settings
        # or reporting of Window Open mode
        #self.add_property(Property_Integer(self, id="away_end", name="Away end", settable=False))
    def update_state(self,thermostat):
        self.get_property('target-temperature').value = thermostat.target_temperature
        self.get_property('valve-state').value = thermostat.valve_state
        self.get_property("low-battery").value = thermostat.low_battery
#    Unknown = -1
#    Closed = 0
#    Open = 1
#    Auto = 2
#    Manual = 3
#    Away = 4
#    Boost = 5
        switcher= {
                0: "Closed",
                1: "Open",
                2: "Auto",
                3: "Manual",
                4: "Away",
                5: "Boost"
        }
        self.get_property("mode").value = switcher.get(thermostat.mode)
        mode = thermostat._raw_mode
        self.get_property("mode-manual").value = mode.MANUAL
        self.get_property("mode-away").value = mode.AWAY
        self.get_property("mode-dst").value = mode.DST
        self.get_property("mode-window").value = mode.WINDOW

        self.get_property("locked").value = thermostat.locked
        self.get_property("boost").value = thermostat.boost
        self.get_property("comfort-temperature").value = thermostat.comfort_temperature
        self.get_property("eco-temperature").value = thermostat.eco_temperature
        self.get_property("temperature-offset").value = thermostat.temperature_offset
        self.get_property("min-temp").value = thermostat.min_temp
        self.get_property("max-temp").value = thermostat.max_temp
        self.get_property("firmware-version").value = thermostat.firmware_version
        self.get_property("device-serial").value = thermostat.device_serial
    def set_target_temperature(self,x):
        l.debug("SETTING target_temp to "+str(x))
        thermostat.target_temperature=x
    def set_locked(self,x):
        thermostat.locked=x
    def set_boost(self,x):
        l.debug("SETTING boost to "+str(x))
        thermostat.boost=x
    def set_temperature_offset(self,x):
        thermostat.temperature_offset=x
    def set_mode_manual(self, x):
        if(x):
           thermostat.mode = 3 #MANUAL
        else:
           thermostat.mode = 0 #AUTO
    def set_mode(self, x):
        #not working yet
        thermostat.mode = x

class Device_EQ3BT(Device_Base):
    def __init__(self, device_id=None, name=None, homie_settings=None, mqtt_settings=None):
        super().__init__ (device_id, name, homie_settings, mqtt_settings)
        self.add_node(Node_EQ3BT(self))
        self.start()
    def update(self,thermostat):
        self.get_node('eq3bt').update_state(thermostat)


homie = Device_EQ3BT(device_id=device_id, name=device_name, mqtt_settings=mqtt_settings)

while True:
        try:
            thermostat.update()
        except Exception as e:
            l.warning(e)
            l.warning("Error connecting to thermostat; trying again")
            time.sleep(10)
            continue
        if thermostat._raw_mode == None:
            l.warning("No reply received from thermostat... Strange!")
            time.sleep(10)
            continue #no message received within acceptable time...
        print(thermostat)
        homie.update(thermostat)
        time.sleep(300)
