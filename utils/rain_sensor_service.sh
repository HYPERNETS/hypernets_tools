#!/bin/bash - 

set -o nounset                              # Treat unset variables as an error
set -euo pipefail							# Bash Stict Mode
IFS=$'\n\t'

close_relay(){
	python -m hypernets.yocto.relay -soff -n4
}

trap "close_relay" EXIT


python -m hypernets.yocto.relay -son -n4

sleep 4

for i in {1..60} ; do 
	python -m hypernets.rain_sensor
	sleep 1
done
