#!/usr/bin/python

# Author: Ruben Faelens, (C) 2021
# Goal: Transmit Klik-Aan-Klik-Uit protocol in python
# Based on NewRemoteSwitch library v1.1.0 by Randy Simons http://randysimons.nl
# GPLv3

import pigpio

class RemoteSwitch:
    pi=None
    periodusec=0
    repeats=0
    def _init_(address, pin, periodusec, repeats):
        self.periodusec=periodusec
        self.repeats=repeats
        self.pi = pigpio.pi()
        pi.set_mode(pin, pigpio.OUTPUT)
        buildWave(True)
        buildWave(False)
    def buildWave(onOff):
        G1=4
        G2=24

        pi.set_mode(G1, pigpio.OUTPUT)
        pi.set_mode(G2, pigpio.OUTPUT)

        flash_500=[] # flash every 500 ms
        flash_100=[] # flash every 100 ms

        #                              ON     OFF  DELAY

        flash_500.append(pigpio.pulse(1<<G1, 1<<G2, 500000))
        flash_500.append(pigpio.pulse(1<<G2, 1<<G1, 500000))

        flash_100.append(pigpio.pulse(1<<G1, 1<<G2, 100000))
        flash_100.append(pigpio.pulse(1<<G2, 1<<G1, 100000))

        pi.wave_clear() # clear any existing waveforms

        pi.wave_add_generic(flash_500) # 500 ms flashes
        f500 = pi.wave_create() # create and save id

        pi.wave_add_generic(flash_100) # 100 ms flashes
        f100 = pi.wave_create() # create and save id

        pi.wave_send_repeat(f500)

    def encodeTelegram(trits):
        long data = 0;
        for i in range(12):
            data *= 3
            data += trits[i]

        data |= self.periodusec << 23
        data |= self.repeats << 20
        return(data)
# Format data:
# pppppppp|prrrdddd|dddddddd|dddddddd (32 bit)
# p = period (9 bit unsigned int
# r = repeats as 2log. Thus, if r = 3, then signal is sent 2^3=8 times
# d = data
    def sendTelegram(data, pin):
        periodusec = data >> 23
        repeats = 5 << (( data >> 20) & 7)
        data = data & 0xffffff # truncate to 20 bit

        long dataBase4 = 0;

        for i in range(12):
                dataBase4<<=2;
                dataBase4|=(data%3);
                data/=3;

        for j in range(repeats):
          #send one telegram

          #use data-var as working var
          data=dataBase4;
          for i in range(12):
               if (data&3) == :

                for (unsigned short i=0; i<12; i++) {
                        switch (data & 3) { // 3 = B11
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec*3);
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec*3);
                                        break;
                                case 1:
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec*3);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec);
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec*3);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec);
                                        break;
                                case 2: //AKA: X or float
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec*3);
                                        digitalWrite(pin, HIGH);
                                        delayMicroseconds(periodusec*3);
                                        digitalWrite(pin, LOW);
                                        delayMicroseconds(periodusec);
                                        break;
                        }
                        //Next trit
                        data>>=2;
                }

                //Send termination/synchronisation-signal. Total length: 32 periods
                digitalWrite(pin, HIGH);
                delayMicroseconds(periodusec);
                digitalWrite(pin, LOW);
                delayMicroseconds(periodusec*31);
        }
}


ool RemoteSwitch::isSameCode(unsigned long encodedTelegram, unsigned long receivedData) {
        return (receivedData==(encodedTelegram & 0xFFFFF)); //Compare the 20 LSB's
}


 
