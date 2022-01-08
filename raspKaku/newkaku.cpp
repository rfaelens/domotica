#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <unistd.h>
#include <ctype.h>
#include <iostream>
#include "NewRemoteTransmitter.cpp"

using namespace std;

int main(int argc, char **argv) 
{
    int pin_out = 15; // Pin out using wiringPi pin numbering scheme (15 = TxD / BCM GPIO 14, see https://projects.drogon.net/raspberry-pi/wiringpi/pins/)
    int device = 0;
    int address = 0;
    bool state = false;
    
    
    if( argc != 4 ) { // not enough arguments
    	std::cout << "usage: " << argv[0] << " address device state" << std::endl;
    	std::cout << "example: " << argv[0] << " M 10 on" << std::endl;
	    return 0;
    } else {
            std::cout << "adress1" << argv[1] << " test " << std::endl;
	    address = atol(argv[1]);
	    device = atol(argv[2]);
	    string statestr = argv[3];
	    
	    if( statestr.compare("on") == 0 ) {
		    state = true;
	    } else {
		    state = false;
	    }
    }
    
    // load wiringPi
	if(wiringPiSetup() == -1)
	{
		printf("WiringPi setup failed. Maybe you haven't installed it yet?");
		exit(1);
	}

    // setup pin and make it low
	pinMode(pin_out, OUTPUT);
	digitalWrite(pin_out, LOW);
//	KaKuSwitch kaKuSwitch(pin_out);
//	kaKuSwitch.sendSignal(address, device, state);
std::cout << "address= " << address << " device= " << device << std::endl;
NewRemoteTransmitter transmitter(address, 15, 260, 3);
transmitter.setAddress(address);
transmitter.sendUnit(device, state);
}


