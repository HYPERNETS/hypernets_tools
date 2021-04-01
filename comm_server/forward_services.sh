#!/usr/bin/bash

# TODO : add args for specify other credentials

if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./comm_server/${0##*/} instead"
	exit 1
fi


ipServer=$(awk -F "= " '/credentials/ {print $2}' config_hypernets.ini)

#ssh -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
#	-R4444:10.42.0.184:4444 $ipServer
#
#ssh -g -N -T -o ServerAliveInterval 10 -o "ExitOnForwardFailure yes" \
#	-R8888:127.0.0.1:8888 $ipServer
