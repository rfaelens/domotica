#!/usr/bin/env python
from homie.device_base import Device_Base
from homie.node.node_contact import Node_Contact
from homie.node.property.property_contact import Property_Contact
from homie.node.property.property_temperature import Property_Temperature
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_boolean import Property_Boolean
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

# Long arduous bugfix...
# see https://github.com/eclipse/paho.mqtt.python/issues/354
settings = {
    'MQTT_BROKER' : 'nas',
    'MQTT_PORT' : 1883,
    'MQTT_SHARE_CLIENT': True
}
mqtt_settings =  homie.mqtt.homie_mqtt_client._mqtt_validate_settings(settings)
class MQTTClientWrapper(Client):
    def publish(self, topic, payload=None, qos=1, retain=False):
       with self._callback_mutex:
            Client.publish(self, topic, payload, qos, retain)
class BugfixClient(PAHO_MQTT_Client):
    def connect(self):
        homie.mqtt.mqtt_base.MQTT_Base.connect(self)
        #self.mqtt_client = MQTTClientWrapper(client_id=self.mqtt_settings['MQTT_CLIENT_ID'])
        self.mqtt_client = Client(client_id=self.mqtt_settings['MQTT_CLIENT_ID'])
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        #self.mqtt_client.on_publish = self._on_publish
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.enable_logger(homie.mqtt.paho_mqtt_client.mqtt_logger)
        self.mqtt_client.enable_logger()
        if self.mqtt_settings ['MQTT_USERNAME']:
            self.mqtt_client.username_pw_set(
                    self.mqtt_settings ['MQTT_USERNAME'],
                    password=self.mqtt_settings ['MQTT_PASSWORD']
            )
        try:
            self.mqtt_client.connect(
                self.mqtt_settings ['MQTT_BROKER'],
                port=self.mqtt_settings ['MQTT_PORT'],
                keepalive=self.mqtt_settings ['MQTT_KEEPALIVE'],
            )
            self.mqtt_client.loop_start()
        except Exception as e:
            homie.mqtt.paho_mqtt_client.logger.warning ('MQTT Unable to connect to Broker {}'.format(e))
clientWithBugfix = BugfixClient(mqtt_settings=mqtt_settings)
clientWithBugfix.connect()
homie.mqtt.homie_mqtt_client.common_mqtt_client = clientWithBugfix
