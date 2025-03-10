#!/bin/bash - 
#===============================================================================
# #          FILE: webcamGetImg.sh
# 
#         USAGE: ./webcamGetImg.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: YOUR NAME (), 
#  ORGANIZATION: 
#       CREATED: 28/11/2019 10:53
#      REVISION: v0.2
#===============================================================================


set -o nounset                              # Treat unset variables as an error
set -euo pipefail							# Bash Stict Mode

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./utils/${0##*/} instead"
	exit 1
fi

IFS=$'\n\t'
YMFolder=$(date +"%Y/%m/")
VERBOSE="" # "-v"

# webcam_get_img "site" "$credent_site" "$ip_site" 5 $is_poe
# webcam_get_img "sky" "$credent_sky" "$ip_sky" 6 $is_poe
webcam_get_img()(
	camname=$1
	credent=$2
	ip=$3
	relay=$4
	is_poe=$5

	if [[ $is_poe -eq 0 ]]; then
		echo "[INFO]  ${camname}_cam: Opening relay $relay"
		python -m hypernets.yocto.relay -n$relay -son
	fi

	echo "[INFO]  ${camname}_cam: Sleeping 60s"
	sleep 60 # empirical

	set +e
	./utils/webcam_get_image.sh -c "$credent" -i "$ip" -d "OTHER/WEBCAM_${camname^^}/$YMFolder" -w $VERBOSE
	retcode=$?
	set -e

	if [[ $retcode -ne 0 ]] ; then
		echo "[ERROR]  ${camname}_cam: image capture failed"
	fi

	if [[ $is_poe -eq 0 ]]; then
		python -m hypernets.yocto.relay -n$relay -soff
		echo "[INFO]  ${camname}_cam: Closing relay $relay"
	fi
)

source utils/configparser.sh

config_site=$(parse_config "webcam_site" config_static.ini)
credent_site=$(echo $config_site | cut -d "@" -f1)
ip_site=$(echo $config_site | cut -d "@" -f2)
poe_cameras=$(parse_config "poe_cameras" config_static.ini)

if [[ "$poe_cameras" == "yes" ]]; then
	is_poe=1
    echo "[INFO]  PoE_cam: Opening relay 5"
    python -m hypernets.yocto.relay -n5 -son
else
	is_poe=0
fi

# check if valid IP
if [[ "$ip_site" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	webcam_get_img "site" "$credent_site" "$ip_site" 5 $is_poe
	pid_site=$!
else
	if [[ $config_site != "" ]]; then
		echo "[WARNING]  Site camera IP '$ip_site' is invalid"
	fi
	pid_site=0
fi

# sleep 1 s so that logs of two cameras are collated
sleep 1

config_sky=$(parse_config "webcam_sky" config_static.ini)
credent_sky=$(echo $config_sky | cut -d "@" -f1)
ip_sky=$(echo $config_sky | cut -d "@" -f2)

# check if valid IP
if [[ "$ip_sky" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	webcam_get_img "sky" "$credent_sky" "$ip_sky" 6 $is_poe
	pid_sky=$!
else
	if [[ $config_sky != "" ]]; then
		echo "[WARNING]  Sky camera IP '$ip_sky' is invalid"
	fi
	pid_sky=0
fi

if [[ "$pid_sky" -ne 0 ]]; then
	wait $pid_sky
	sleep 1
fi

if [[ "$pid_site" -ne 0 ]]; then
	wait $pid_site
fi

if [[ $is_poe -eq 1 ]]; then
    echo "[INFO]  PoE_cam: Closing relay 5"
    python -m hypernets.yocto.relay -n5 -soff
else
    is_poe=0
fi

