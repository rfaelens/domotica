# The nibegw program does the following things
# 1) Open serial port, throw away any spurious bytes
# 2) When receiving a 0x69 (start message), read in the message
# 3) Relay the message to UDP
# 4) AND send an ACK or NAK to the heat pump

# socat -u UDP4-RECVFROM:9999,fork,reuseaddr,readbytes=32 SYSTEM:"hexdump -C"
import paho.mqtt.client as mqtt

import socket
import asyncio
from crccheck.checksum import ChecksumXor8
## https://tinkering.xyz/async-serial/
class FrameReader(asyncio.Protocol):
    def connection_made(self, transport):
        """Store the serial transport and prepare to receive data.
        """
        print('Reader connection created')

    def datagram_received(self, data, addr):
        """Parse bytes into message
        """
#        print("UDP received: ", data.hex() )
        self.parseBuffer(data)

        #	Frame format coming FROM heat pump: (0x20 means destination = MODBUS40)
        # +----+----+----+-----+-----+----+----+-----+
        # | 5C | 00 | 20 | CMD | LEN |  DATA   | CHK |
        # +----+----+----+-----+-----+----+----+-----+
        # What is the last byte???
    def parseBuffer(self, msg):
#        while len(self.buf) >= 6: #at least 6 bytes
#            if self.buf[0:3] != bytes([0x5c, 0x00, 0x20]): # start message
#                print("Skipping spurious bytes: ", self.buf[0:3].hex()) ## this should not happen!!!
#                self.buf = self.buf[ 3:len(self.buf) ]
#                continue
            cmd = msg[3]
            datalen = int(msg[4])
#            if len(self.buf) < datalen + 6:
#                print("Wait until buffer fills..")
#                break #incomplete message, wait until buffer fills

            data = msg[5:5+datalen]
            crc = msg[ 5+datalen ]
            mysteryByte = msg[6+datalen]
            calcCrc = ChecksumXor8()
            calcCrc.process(msg[1:datalen+6-1])
#            print("Frame received ", msg.hex(), " length ", len(msg),": calcCrc=", calcCrc.finalhex() )
            if calcCrc.final() != crc: print("CRC failed")
            self.handleFrame(cmd, data)
    def handleFrame(self, cmd, data):
        #commands: 0x68, 0x69, 0x6a, 0x6b, 0x6d, 0xee
        # 0x68 report multiple
        # 0x69 no data   READ token  :heat pump says: if you want, you can read something now. If not, just send ACK.
        # 0x6B           WRITE token :heat pump says: if you want, you can write something. If not, just send ACK.
        # 0x6a read single
        # 0x6d some data ???
        # 0xee nothing
        if cmd == 0x68:
          self.handleData(data)
        elif cmd == 0x69: #read token
          True #nibegw has interpreted this message and knows this is the time to relay READ requests from UDP socket
        elif cmd == 0x6a: #single read
          self.handleRead(data)
        elif cmd == 0x6b: #write token
          True #nibegw has interpreted this message, and knows this is the time to relay WRITE requests from UDP socket
        elif cmd == 0x6c: #write confirmation
          self.handleWriteConfirmation(data)
        #elif cmd == 0x6d:
        #  True
        #elif cmd == 0xee:
        #  True
        else:
          print("unknown cmd:  0x", cmd.to_bytes(1, 'big').hex(), " (data: ", data.hex(), ")" )
    def handleWriteConfirmation(self, data):
        print("0x6c WRITE CONFIRMED:  0x", data.hex())
    def handleRead(self, data):
        #print("READ: 0x", data.hex())
        register = data[1]*256 + data[0]
        if not register in definition:
          print("Unknown register 0x", data[0:2].hex(), " (", register, ") skipping...")
          return
        registerDefinition = definition[register]
        dataType = registerDefinition[4]
        length = { "u8":1, "s8":1, "u16":2, "s16":2, "u32":4, "s32":4 }
        signed = { "u8":False, "s8":True, "u16":False, "s16":True, "u32":False, "s32":True }
        ## TODO: handle 32-bit numbers
        if length[dataType] == 4: raise "Error: no support for 32bit numbers yet"
        value = data[2:2+length[dataType] ]
        value = int.from_bytes(value, "little", signed=signed[dataType] )
        factor = int( registerDefinition[5] )
        value = value / factor
        #value = str(value) + registerDefinition[3] #unit
        print("0x6a READ: ", register, "(",dataType,") = ", value)
        registers = dict()
        registers[register] = value
        publishData(registers)
        
    def handleData(self, data):
        print( "DATA: 0x", data.hex() )
        registers = dict()
        while len(data) > 0:
          msg = data[0:4]
          data = data[4:len(data)]
          register = msg[1]*256 + msg[0]
          if register == 0xffff:
            continue # empty spot
          elif not register in definition:
            print("Unknown register 0x", data[0:2].hex(), "skipping...")
            continue
          registerDefinition = definition[register]
          dataType = registerDefinition[4]
          length = { "u8":1, "s8":1, "u16":2, "s16":2, "u32":4, "s32":4 }
          signed = { "u8":False, "s8":True, "u16":False, "s16":True, "u32":False, "s32":True }
          ## TODO: handle 32-bit numbers
          if length[dataType] == 4: raise "Error: no support for 32bit numbers yet"
          value = msg[2:4 ]
          value = int.from_bytes(value, "little", signed=signed[dataType] )
          factor = int( registerDefinition[5] )
          value = value / factor
#          value = str(value) + registerDefinition[3] #unit
          registers[register] = value
        publishData(registers)
        print("0x68 DATA:", registers )
    def connection_lost(self, exc):
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
    print("Generated READ request for ", register,":", msg.hex() )
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
    msg += (value*factor).to_bytes(4, "little", signed=signed[dataType])
    calcCrc = ChecksumXor8()
    calcCrc.process(msg)
    msg += calcCrc.finalbytes()
    print("Generated WRITE request for ", register,"<-",value,":", msg.hex() )
    return(msg)
    

sock = socket.socket(socket.AF_INET,
                     socket.SOCK_DGRAM)
#sock.sendto(getReadRequest(43086), ("127.0.0.1", 10000))

definition = dict()
#definition[ 0xffff ] = [ "Empty register", "", 0xffff, "", "u16", "1", "0", "0", "0", "R" ]
import csv
import json

def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    print("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe("nibe/modbus/+/get")
    client.subscribe("nibe/modbus/+/set")

def on_message(client, userdata, msg):
    print("Message received-> " + msg.topic + " " + str(msg.payload))  # Print a received msg

def publishData(registers):
  for register in registers:
    value = registers[register]
    client.publish("nibe/modbus/"+str(register)+"/raw", value)
    registerDefinition = definition[register]
    config = {"register":register,"value":value,"unit":registerDefinition[3],"factor":registerDefinition[5],"type":registerDefinition[4],"mode":registerDefinition[8],"titel":registerDefinition[0],"info":registerDefinition[1],"min":registerDefinition[6],"max":registerDefinition[7]}
    client.publish("nibe/modbus/"+str(register)+"/config", json.dumps(config))

client=mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("127.0.0.1")
client.loop_start()


if __name__ == '__main__':
  with open('registers.csv', encoding='iso-8859-1') as csvfile:
    reader = csv.reader(csvfile, delimiter=";")
    for row in reader:
      if len(row) < 5: continue
      if row[2] == "ID": continue #header row
      register = int(row[2])
      definition[register] = row

#  sock.sendto( getWriteRequest(43005, 10), ("127.0.0.1", 10001))
  loop = asyncio.get_event_loop()
  t = loop.create_datagram_endpoint(FrameReader, local_addr=('0.0.0.0', 9999))
  loop.run_until_complete(t) # Server starts listening
  loop.run_forever()
