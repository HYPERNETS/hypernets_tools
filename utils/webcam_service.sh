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
	echo "Sleeping 60s"
	sleep 60 # empirical
	config_site=$(awk -F "[ =]+" '/webcam_site/ {print $2; exit}' config_static.ini)
	credent_site=$(echo $config_site | cut -d "@" -f1)
	ip_site=$(echo $config_site | cut -d "@" -f2)
	./utils/webcam_get_image.sh -c "$credent_site" -i "$ip_site" -d "OTHER/WEBCAM_SITE/" -wv
	echo "Sleeping 30s"
	sleep 30
	python -m hypernets.yocto.relay -n5 -soff
	echo "Closing relay 5"
}

webcam_sky(){
	echo "Sleeping 60s"
	sleep 60 # empirical
	config_sky=$(awk -F "[ =]+" '/webcam_sky/ {print $2; exit}' config_static.ini)
	credent_sky=$(echo $config_sky | cut -d "@" -f1)
	ip_sky=$(echo $config_sky | cut -d "@" -f2)
	./utils/webcam_get_image.sh -c "$credent_sky" -i "$ip_sky" -d "OTHER/WEBCAM_SKY/" -wv
	echo "Sleeping 30s"
	sleep 30
	python -m hypernets.yocto.relay -n6 -soff
	echo "Closing relay 6"
}

echo "Opening relay 5"
python -m hypernets.yocto.relay -n5 -son
sleep 1
echo "Opening relay 6"
python -m hypernets.yocto.relay -n6 -son

webcam_sky &
pid_sky=$!
webcam_site &
pid_site=$!

wait $pid_sky
sleep 1
wait $pid_site
