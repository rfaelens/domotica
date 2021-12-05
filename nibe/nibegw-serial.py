# The nibegw program does the following things
# 1) Open serial port, throw away any spurious bytes
# 2) When receiving a 0x69 (start message), read in the message
# 3) Relay the message to UDP
# 4) AND send an ACK or NAK to the heat pump

# socat -u UDP4-RECVFROM:9999,fork,reuseaddr,readbytes=32 SYSTEM:"hexdump -C"

import socket
import asyncio
from serial import Serial
from crccheck.checksum import ChecksumXor8
import collections
import threading

registersFile = '/opt/domotica/nibe/registers.csv'
homeAssistantFile = '/opt/domotica/nibe/homeassistant.yaml'

readRequest = collections.deque()
writeRequest = collections.deque()
lock = threading.Lock()
startup = True
hpIdentifier = None

poll = collections.deque()

def parseBuffer(msg):
            if len(msg) == 1 and msg[0] == 0x06:
              #print("0x06 ACK from HP")
              return()
            cmd = msg[3]
            datalen = int(msg[4])
            data = msg[5:5+datalen]
            crc = msg[ 5+datalen ]
            #mysteryByte = msg[6+datalen]
            calcCrc = ChecksumXor8()
            calcCrc.process(msg[1:datalen+6-1])
            if calcCrc.final() != crc: print("CRC failed for 0x"+msg.hex())
            handleFrame(cmd, data)
def handleFrame(cmd, data):
        data = data.replace(b'\\\\', b'\\') # b'\\' is 0x5c, which is 'escaped' in the message
        #commands: 0x68, 0x69, 0x6a, 0x6b, 0x6d, 0xee
        # 0x68 report multiple
        # 0x69 no data   READ token  :heat pump says: if you want, you can read something now. If not, just send ACK.
        # 0x6B           WRITE token :heat pump says: if you want, you can write something. If not, just send ACK.
        # 0x6a read single
        # 0x6d broadcasts heatpump identifier
        # 0xee nothing
        if cmd == 0x68:
          handleData(data)
        elif cmd == 0x69: #read token
          handleReadToken(data)#now is the time to relay READ requests
        elif cmd == 0x6a: #single read
          handleRead(data)
        elif cmd == 0x6b: #write token
          handleWriteToken(data) #now is the time to relay WRITE requests
        elif cmd == 0x6c: #write confirmation
          handleWriteConfirmation(data)
        elif cmd == 0x6d: #system identification
          handleAdvertisement(data)
        #elif cmd == 0x6d:
        #  True
        #elif cmd == 0xee:
        #  True
        else:
          print("unknown cmd:  0x", cmd.to_bytes(1, 'big').hex(), " (data: ", data.hex(), ")" )
          sendAck(ser)

def handleAdvertisement(data):
     print("0x6d ADVERTISEMENT: ", data, "  0x", data.hex())
     global hpIdentifier
     hpIdentifier = data[4:].decode()
     sendAck(ser)

def sendAck(ser):
#    print("ACK")
    ser.write(0x06)
#    ser.read() #read the byte; RS-485

def handleWriteToken(data):
#        print("0x6b WRITE TOKEN:  0x", data.hex())
        if len(writeRequest) >= 1:
            req = writeRequest.popleft()
            print("\tsending "+req.hex())
            ser.write(req)
            register = req[4]*256 + req[3]
            readRequest.appendleft(getReadRequest(register))
        else:
            sendAck(ser)
def handleReadToken(data):
#        print("0x69 READ TOKEN:  0x", data.hex())
        if len(readRequest) >= 1:
            req = readRequest.popleft()
            print("\tsending "+req.hex())
            ser.write(req)
        else:
            if len(poll) == 0:
              sendAck(ser)
            else:
              with lock: #send one of the POLL
                register = poll.popleft()
                poll.append(register)
                req = getReadRequest(register)
                ser.write(req)
def handleWriteConfirmation(data):
#        print("0x6c WRITE CONFIRMED:  0x", data.hex())
        sendAck(ser)

def handleRead(data):
        print("READ: 0x", data.hex())
        ## if data contains 0x5c, it is repeated ("escaped")
        if len(data) != 6:
            print("Malformed READ packet; size "+str(len(data)))
        register = data[1]*256 + data[0]
        if not register in definition:
          print("Unknown register 0x", data[0:2].hex(), " (", register, ") skipping...")
          return
        registerDefinition = definition[register]
        row = registerDefinition
        dataType = registerDefinition[4]
        length = { "u8":1, "s8":1, "u16":2, "s16":2, "u32":4, "s32":4 }
        signed = { "u8":False, "s8":True, "u16":False, "s16":True, "u32":False, "s32":True }
        value = data[2:2+length[dataType] ]
        value = int.from_bytes(value, "little", signed=signed[dataType] )
        minRaw = int(registerDefinition[6])
        maxRaw = int(registerDefinition[7])
        useLimits = not ( (minRaw == maxRaw) and (maxRaw == 0) )
        if useLimits and (value < minRaw or value > maxRaw):
            print("Received faulty value for register "+str(register)+": "+str(value)+", not relaying to MQTT!")
            return()
        factor = int( registerDefinition[5] )
        value = value / factor
        strvalue = str(value) + registerDefinition[3] #unit
#        print("0x6a READ: ", register, "(",dataType,") = ", strvalue)
        mqttc.publish("nibe/"+str(register)+"/value", str(value))
        config = '{"register":'+str(register)+',"title":"'+row[0]+'","info":"'+row[1]+'","Unit":"'+row[3]+'","Min":"'+row[6]+'","Max":"'+row[7]+'","Default":"'+row[8]+'","Mode":"'+row[9]+'","Value":'+str(value)+'}'
        mqttc.publish("nibe/"+str(register)+"/config", config)
        sendAck(ser)

        global startup
        if startup and register == 45001 and value == 251:
            print("Initial boot, alarm is MODBUS ALARM. Resetting...")
            startup = False #reset startup
            writeRequest.append( getWriteRequest(45171, 1) ) #reset the alarm

advertisedData = False #have we advertised the values we receive from Data packet ?
def handleData(data):
        global advertisedData
        #print( "DATA: 0x", data.hex() )
        registers = dict()
        while len(data) > 0:
          msg = data[0:4]
          data = data[4:len(data)]
          register = msg[1]*256 + msg[0]
          if register == 0xffff:
            continue # empty spot
          elif register == 0x0000:
            continue # empty spot
          elif not register in definition:
            print("Unknown register 0x", msg[0:2].hex(), "skipping...")
            continue
          registerDefinition = definition[register]
          row = registerDefinition
          dataType = registerDefinition[4]
          length = { "u8":1, "s8":1, "u16":2, "s16":2, "u32":4, "s32":4 }
          signed = { "u8":False, "s8":True, "u16":False, "s16":True, "u32":False, "s32":True }
          if length[dataType] == 4:
              if len(data) == 0:
                  print("ERROR: 32-bit register at end of DATA packet")
                  continue
              msg = msg + data[2:4] # add next register
              data = data[4:len(data)]
          value = msg[2:2+length[dataType] ]
          value = int.from_bytes(value, "little", signed=signed[dataType] )
          minRaw = int(registerDefinition[6])
          maxRaw = int(registerDefinition[7])
          useLimits = not ( (minRaw == maxRaw) and (maxRaw == 0) )
          if useLimits and (value < minRaw or value > maxRaw):
            print("Received faulty value for register "+str(register)+": "+str(value)+", not relaying to MQTT!")
            continue
          factor = int( registerDefinition[5] )
          value = value / factor
          strvalue = str(value) + registerDefinition[3] #unit
          ## TODO: maybe delay this until after sending ACK?
          #print("0x68 DATA 0x", msg.hex(), ":", register, "(",dataType,") = ", strvalue)
          mqttc.publish("nibe/"+str(register)+"/value", str(value))
          config = '{"register":'+str(register)+',"title":"'+row[0]+'","info":"'+row[1]+'","Unit":"'+row[3]+'","Datatype":"'+row[4]+'","factor":"'+row[5]+'","Min":"'+row[6]+'","Max":"'+row[7]+'","Default":"'+row[8]+'","Mode":"'+row[9]+'","Value":'+str(value)+'}'
          mqttc.publish("nibe/"+str(register)+"/config", config)

          registers[register] = value
#        print("0x68 DATA:", registers )
        sendAck(ser)

        ## ensure HA knows about this Data
        global advertisedData
        global hpIdentifier
        if advertisedData == False and hpIdentifier != None:
            print("Advertising to HomeAssistant...")
            for register in registers.keys():
                print("advertising register "+str(register))
                res = advertiseHomeassistant(register)
                print(res)
                if res.rc != mqtt.MQTT_ERR_SUCCESS:
                    print("Server not connected yet, retrying later...")
                    return()
            advertisedData = True
def connection_lost(exc):
        print('Reader closed')


def getReadRequest(register):
    # 0xc0: not a clue
    # 0x69: command? (read request)
    # command length
    # register byte1
    # register byte 2
    # checksum
    msg = bytes([0xc0, 0x69, 0x02])
    msg += register.to_bytes(2, "little")
    calcCrc = ChecksumXor8()
    calcCrc.process(msg)
    msg += calcCrc.finalbytes()
    #print("Generated READ request for ", register,":", msg.hex() )
    return(msg)

def getWriteRequest(register, value):
    registerDefinition = definition[register]
    mode = registerDefinition[9]
    if mode != "R/W": return(bytes())
    msg = bytes([0xc0, 0x6b, 0x06])
    msg += register.to_bytes(2, "little")
    factor = int( registerDefinition[5] )
    dataType = registerDefinition[4]
    signed = { "u8":False, "s8":True, "u16":False, "s16":True, "u32":False, "s32":True }
    msg += int((value*factor)).to_bytes(4, "little", signed=signed[dataType])
    calcCrc = ChecksumXor8()
    calcCrc.process(msg)
    msg += calcCrc.finalbytes()
    print("Generated WRITE request for ", register,"<-",value,":", msg.hex() )
    return(msg)
    
def checkMessage(msg):
    if len(msg) == 1:
        if msg[0] == 0x5c:
            return 0 #wait for more data
        elif msg[0] == 0x06:
            return 1 #ACK message
        else:
            return -1 #bad message
    if len(msg) >= 2 and msg[1] != 0x00:
        return -1
    if len(msg) < 6:
        return 0 #not yet ready
    datalen = int(msg[4])
    if len(msg) < datalen + 6:
        return 0
    return datalen + 6

import csv
definition = dict()
with open(registersFile, encoding='iso-8859-1') as csvfile:
    reader = csv.reader(csvfile, delimiter=";")
    for row in reader:
      if len(row) < 5: continue
      if row[2] == "ID": continue #header row
      register = int(row[2])
      definition[register] = row

import regex
topicre = regex.compile('^nibe/(\\d+)/([^/]*)$')
def on_message(client, userdata, message):
#    print("Received message '" + str(message.payload) + "' on topic '"
#                    + message.topic + "' with QoS " + str(message.qos))
    try:
      m = topicre.match(message.topic)
      register=int(m.group(1))
      action=m.group(2)
    except:
        print("Failed to parse MQTT Topic "+message.topic)
        return()
#    print(action+" on register <"+str(register)+">")
    if action == "value":
        True #this is my own message
    elif action == "config":
        True #this is my own message
    elif action == "read":
      readRequest.append( getReadRequest(register) )
    elif action == "write":
      try:
          value = float(message.payload)
          writeRequest.append( getWriteRequest(register, float(message.payload)) )
      except:
          print("Invalid write value for register "+register+": <"+message.payload+">")
    elif action == "unpoll":
      with lock:
        if register in poll:
          poll.remove(register)
    elif action == "poll":
      with lock:
        if not register in poll:
          poll.append(register)
          advertiseHomeassistant(register)
    else:
      print("Unknown action: "+action)

import json
import time

def advertiseHomeassistant(register):
    registerDefinition = definition[register]
    register = str(register)
    advertisement = dict()
    advertisement['state_topic'] = 'nibe/'+register+'/value'
    advertisement['json_attributes_topic'] = 'nibe/'+register+'/config'
    mode = registerDefinition[9]
    unit = registerDefinition[3]
    if mode == "R":
        advType = "sensor"
        advertisement['expire_after'] = 1 * 60 * 60 #1 hour
        advertisement['unit_of_measurement'] = unit
        if unit == "°C":
            advertisement['device_class'] = 'temperature'
        elif unit == "%":
            advertisement['device_class'] = 'power_factor'
        elif unit == "kWh" or unit == "Wh":
            advertisement['device_class'] = 'energy'
            advertisement['state_class'] = 'total_increasing'
        elif unit == "W" or unit == "kW":
            advertisement['device_class'] = 'power'
        elif unit == "A":
            advertisement['device_class'] = 'current'
        elif unit == "Hz":
            True
    #        advertisement['device_class'] = ''
        elif unit == "h":
            True
    #        advertisement['device_class'] = ''
        elif unit == "":
            True
    #        advertisement['device_class'] = ''
        else:
            print("Unknown unit mapping: "+unit)
    elif mode == "R/W":
        advType = "number"
        advertisement['command_topic'] = 'nibe/'+register+'/write'
        minR = registerDefinition[6]
        maxR = registerDefinition[7]
        factor = int( registerDefinition[5] )
        useLimits = not ( (minR == maxR) and (maxR == "0") )
        if useLimits:
            advertisement['min'] = int(registerDefinition[6]) / factor
            advertisement['max'] = int(registerDefinition[7]) / factor
    else:
        print("Unknown mode: "+mode)
        return()
    device = dict()
    global hpIdentifier
    device['identifiers'] = hpIdentifier
    device['manufacturer'] = "NIBE"
    advertisement['device'] = device
    advertisement['unique_id'] = 'nibe_'+register
#    config = '{"register":'+str(register)+',"title":"'+row[0]+'","info":"'+row[1]+'","Unit":"'+row[3]+'","Min":"'+row[6]+'","Max":"'+row[7]+'","Default":"'+row[8]+'","Mode":"'+row[9]+'","Value":'+str(value)+'}'
    advertisement['name'] = registerDefinition[0]

    res = mqttc.publish("homeassistant/"+advType+"/nibe_"+register+"/config", json.dumps(advertisement), retain=True)
    return(res)

def on_connect(client, userdata, flags, rc):
    print("CONNECTED TO MQTT")
    mqttc.subscribe("nibe/+/+")
    # Open the file and load the file
#    with open(homeAssistantFile) as f:
#        data = yaml.load_all(f, Loader=SafeLoader)
#        print(data)
#    print('Advertising presence for '+str(devices))
#    for device in devices:
#        device = str(device)
#        topic='kaku/M_'+device
#        print("advertising "+device+" at "+topic)
#        mqttc.publish("homeassistant/switch/living_kaku_"+device+"/config", '{"~":"'+topic+'", "name":"living_kaku_'+device+'", "unique_id": "living_kaku_'+device+'", "command_topic":"~/set"}')
#        mqttc.subscribe(topic+"/set")
#    print("done")

import paho.mqtt.client as mqtt
mqttc=mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.connect_async("nas")

from threading import Timer

def startMqtt():
    global hpIdentifier
    while hpIdentifier == None:
        print("Heatpump identifier still not known; sleeping...")
        time.sleep(5)
    mqttc.loop_start()

t = Timer(10.0, startMqtt)
t.start()

# read ALARM state on boot
readRequest.append( getReadRequest(45001) )

ser = Serial('/dev/ttyUSB0', baudrate=9600, timeout=120)
msg = bytearray()
while True:
    msg += bytearray(ser.read())
    msgOk = checkMessage(msg)
    if msgOk == -1:
        print("bad message: "+msg.hex())
        msg.clear()
        continue
    if msgOk == 0: #not yet ready
#        print(".", end="")
        continue
#    print("OK message: "+msg.hex())
    parseBuffer(msg)
    msg.clear()
    #OK, b is 0x5C
#    print(msg.hex())


