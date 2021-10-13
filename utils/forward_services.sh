#!/usr/bin/bash

# TODO : add args for specify other credentials
if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./utils/${0##*/} instead"
	exit 1
fi


source utils/configparser.sh
ipServer=$(parse_config "credentials" config_static.ini)

sshPort=$(parse_config "ssh_port" config_static.ini)

if [ -z $sshPort ]; then
	sshPort="22"
fi

echo $ipServer:$sshPort

# TODO : replace by yocto_ip here :
# ssh -g -N -T -o ServerAliveInterval 10 -o "ExitOnForwardFailure yes" \
# 	-R4444:10.42.0.184:4444 $ipServer

# ssh -v -p $sshPort -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
# 	-R5555:127.0.0.1:4444 $ipServer

ssh -v -p $sshPort -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
	-R5555:10.42.0.76:4444 $ipServer

# ssh -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
# 	-R8888:127.0.0.1:8888 $ipServer
