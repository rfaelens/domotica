#!/usr/bin/env python

import time
import RPi.GPIO as GPIO

def main():

    # tell the GPIO module that we want to use the 
    # chip's pin numbering scheme
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(22,GPIO.IN)


#    GPIO.output(25,True)

    while True:
        if GPIO.input(22):
             print "button true"
        else:
             print "button false"

        time.sleep(0.1)

    print "button pushed"

    GPIO.cleanup()



if __name__=="__main__":
    main()
