#!/usr/bin/bash


set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
    echo "This script must be run from hypernets_tools folder" 1>&2
    echo "Use : ./utils/${0##*/} instead"
    exit 1
fi

systemctl status yvirtualhub --no-pager
echo "Date/Time of the computer:"
date +"%Y/%m/%d %H:%M:%S%z"

echo "Getting Yocto-Pictor-WiFi's Date/Time"

source utils/configparser.sh

yoctoPrefix2=$(parse_config "yocto_prefix2" config_static.ini)
YoctoRTC=$(wget -O- http://127.0.0.1:4444/bySerial/$yoctoPrefix2/api/realTimeClock/dateTime)
err=$?

if [ $err -eq 0 ] ; then
	echo "Yocto RTC : $YoctoRTC"
	echo "Mise à jour de l'heure du PC"
	sudo date -s "$YoctoRTC"  +"%Y/%m/%d %H:%M:%S%z"
	echo "Heure corrigée du PC"
	date +"%Y/%m/%d %H:%M:%S%z"
else
	echo "Error: fail to get YoctoRTC (wget outputs $err)"
fi
