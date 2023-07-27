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
IFS=$'\n\t'

webcam_site(){
	echo "[INFO]  site_cam: Sleeping 60s"
	sleep 60 # empirical
	./utils/webcam_get_image.sh -c "$credent_site" -i "$ip_site" -d "OTHER/WEBCAM_SITE/" -wv
	echo "[INFO]  site_cam: Sleeping 30s"
	sleep 30
	python -m hypernets.yocto.relay -n5 -soff
	echo "[INFO]  Closing relay 5"
}

webcam_sky(){
	echo "[INFO]  sky_cam: Sleeping 60s"
	sleep 60 # empirical
	./utils/webcam_get_image.sh -c "$credent_sky" -i "$ip_sky" -d "OTHER/WEBCAM_SKY/" -wv
	echo "[INFO]  sky_cam: Sleeping 30s"
	sleep 30
	python -m hypernets.yocto.relay -n6 -soff
	echo "[INFO]  Closing relay 6"
}

config_site=$(awk -F "[ =]+" '/webcam_site/ {print $2; exit}' config_static.ini)
credent_site=$(echo $config_site | cut -d "@" -f1)
ip_site=$(echo $config_site | cut -d "@" -f2)

# check if valid IP
if [[ "$ip_site" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	echo "[INFO]  Opening relay 5"
	python -m hypernets.yocto.relay -n5 -son
	webcam_site &
	pid_site=$!
else
	echo "[WARNING] Site camera IP '$ip_site' is invalid"
	pid_site=0
fi

sleep 1

config_sky=$(awk -F "[ =]+" '/webcam_sky/ {print $2; exit}' config_static.ini)
credent_sky=$(echo $config_sky | cut -d "@" -f1)
ip_sky=$(echo $config_sky | cut -d "@" -f2)

# check if valid IP
if [[ "$ip_sky" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	echo "[INFO]  Opening relay 6"
	python -m hypernets.yocto.relay -n6 -son
	webcam_sky &
	pid_sky=$!
else
	echo "[WARNING] Sky camera IP '$ip_sky' is invalid"
	pid_sky=0
fi

if [[ "$pid_sky" -ne 0 ]]; then
	wait $pid_sky
	sleep 1
fi

if [[ "$pid_site" -ne 0 ]]; then
	wait $pid_site
fi

