#!/usr/bin/python

# Author: Ruben Faelens, (C) 2021
# Goal: Transmit Klik-Aan-Klik-Uit protocol in python
# Based on NewRemoteSwitch library v1.1.0 by Randy Simons http://randysimons.nl
# GPLv3
import pigpio

def buildFrame(address, device, state):
    if ord(address) < 65:
        print("Error: wrong address! Should be between A and Z")
    if ord(address) > 90:
        print("Error: wrong address! Should be between A and Z")
    frame = [0]*12
    address = ord(address)
    address -= 65
    for i in range(4):
        frame[i] = 2 if ((address>>i)&1)==1 else 0
    
    device -= 1 # device starts at 0
    for i in range(4):
        frame[i+4] = 2 if ((device>>i)&1)==1 else 0
    
    frame[8] = 0
    frame[9] = 2
    frame[10] = 2
    frame[11] = 2 if state else 0
    return(frame)

def buildWave(frame, period, pin):
    wave = []
    for trit in frame:
        if trit == 0:
            # H L L L H L L L
            wave.append(pigpio.pulse(1<<pin, 0, period))
            wave.append(pigpio.pulse(0, 1<<pin, period*3))
            wave.append(pigpio.pulse(1<<pin, 0, period))
            wave.append(pigpio.pulse(0, 1<<pin, period*3))
        elif trit == 1:
            # H H H L H H H L
            wave.append(pigpio.pulse(1<<pin, 0, period*3))
            wave.append(pigpio.pulse(0, 1<<pin, period))
            wave.append(pigpio.pulse(1<<pin, 0, period*3))
            wave.append(pigpio.pulse(0, 1<<pin, period))
        elif trit == 2:
            # H L L L H H H L
            wave.append(pigpio.pulse(1<<pin, 0, period))
            wave.append(pigpio.pulse(0, 1<<pin, period*3))
            wave.append(pigpio.pulse(1<<pin, 0, period*3))
            wave.append(pigpio.pulse(0, 1<<pin, period))
        else:
            print("Invalid trit: "+trit)
    wave.append(pigpio.pulse(1<<pin, 0, period))
    wave.append(pigpio.pulse(0, 1<<pin, period*31))
    return(wave)

