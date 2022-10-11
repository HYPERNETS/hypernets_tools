#!/usr/bin/bash


systemctl status yvirtualhub --no-pager

# sleep 15
echo "Date/Time of the computer:"
date +"%Y/%m/%d %H:%M:%S%z"

echo "Getting Yocto-Pictor-WiFi's Date/Time"
yocto_prefix2=$(parse_config "yocto_prefix2" config_static.ini)
YoctoRTC=$(wget -O- http://127.0.0.1:4444/bySerial/$yocto_prefix2/api/realTimeClock/dateTime)
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
