#!/bin/sh

while 
	if echo 'info 78:44:05:77:0B:02' | bluetoothctl | grep Connected | grep yes; then
		echo "Already connected"
	else
		echo 'connect 78:44:05:77:0B:02' | bluetoothctl
	fi
	echo 'Sleeping 15s...'
	sleep 15
do
        :
done
