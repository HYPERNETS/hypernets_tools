#!/usr/bin/bash

# TODO : add args for specify other credentials

if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./install/${0##*/} instead"
	exit 1
fi

ssh -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" -R4444:10.42.0.184:4444 hypernets@oceane.obs-vlfr.fr

ssh -g -N -T -o ServerAliveInterval 10 -o ExitOnForwardFailure yes -R8888:127.0.0.1:8888 hypernets@oceane.obs-vlfr.fr
