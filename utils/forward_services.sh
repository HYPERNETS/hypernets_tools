#!/usr/bin/bash

# TODO : add args for specify other credentials
if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./utils/${0##*/} instead"
	exit 1
fi


source utils/configparser.sh

ipServer=$(parse_config "credentials" config_static.ini)
sshPort=$(parse_config "ssh_port" config_static.ini)
forwardPort=$(parse_config "forward_port" config_static.ini)

if [ -z $sshPort ]; then
	sshPort="22"
fi

if [ -z $forwardPort ]; then
	forwardPort="5555"
fi

webcamSite=$(parse_config "webcam_site" config_static.ini)
webcamSky=$(parse_config "webcam_sky" config_static.ini)

ipSky=$(echo $webcamSky | cut -d "@" -f2)
ipSite=$(echo $webcamSite | cut -d "@" -f2)

echo "[DEBUG]  $ipServer:$sshPort --> [$forwardPort]"
echo "[DEBUG]  IP VirtualHub   : 127.0.0.1" 
echo "[DEBUG]  IP Webcam Site  : $ipSite" 
echo "[DEBUG]  IP Webcam Sky   : $ipSky"



PS3="Select the service that you want to forward : "
options=("VirtualHub" "Camera Site" "Camera Sky" 
	"Jupyter Notebook" "Quit")

select opt in "${options[@]}"
do
	case $opt in
		"VirtualHub")
			echo "You choose : $opt"
			service="127.0.0.1:4444"
			break
			;;
		"Camera Site")
			echo "You choose : $opt"
			service="$ipSite:554"
			break
			;;
		"Camera Sky")
			echo "You choose : $opt"
			service="$ipSky:554"
			break
			;;
		"Jupyter Notebook")
			echo "You choose : $opt"
			service="127.0.0.1:8888"
			break
			;;


		"Quit")
			break
			;;
		*) echo "Invalid option $REPLY";;
	esac
done

# TODO : ping before ?

echo "[DEBUG] service : $service"

ssh -v -p $sshPort -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
	-R$forwardPort:$service $ipServer

exit 0

# ssh -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
# 	-R8888:127.0.0.1:8888 $ipServer
