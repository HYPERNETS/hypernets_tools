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

# TODO : Lorsque le timeout est dépassé (webcam hors ligne)
#        > return 1 + stderr

set -o nounset                              # Treat unset variables as an error
set -euo pipefail							# Bash Stict Mode
IFS=$'\n\t'

function usage(){
	printf "Usage %s [-d][-i][-hvw] :\n" "$0"
	printf "  -v  Verbose Mode.\n"
	printf "  -w  Wait on webcam is up.\n"
	printf "  -d, OUTPUT_DIR   Specify the output directory.\n"
	printf "  -f, FILEPREFIX	Specify the file name prefix.\n"
	printf "  -i, IP_ADDRESS   Specify the ip address of the camera.\n"
	printf "  -c, USER:PASS    Specify credentials camera.\n"
	printf "  -h, --help       Diplay this help message.\n"
	printf " Note : default is current directory if not specified.\n"
	exit 0
}

function take_picture(){
	mkdir -p "$OUTPUT_DIR"
	DATE=$(date +"%Y%m%dT%H%M%S") 

	if [ "$VERBOSE" -eq 1 ] ; then
		loglevel=32
	else
		loglevel=24
	fi
	ffmpeg -v $loglevel -y -i rtsp://"$CREDENTIALS$IP_ADDRESS":554 -update 1 -frames:v 1 \
		"$OUTPUT_DIR/$FILEPREFIX$DATE.jpg"

	if [[ $? -eq 0 ]] ; then
		echo "[INFO]  Output File is : '$OUTPUT_DIR/$FILEPREFIX$DATE.jpg'"
	fi
}

function wait_up(){

	# Ping the camera until it starts
	# Timeout : 1 min
	timeout=60

	if [ "$VERBOSE" -eq 1 ] ; then
		echo "[DEBUG]  Waiting for $IP_ADDRESS..."
	fi

	p=1 ; i=1
	while [[ $p -ne 0 ]] && [[ $i -le $timeout ]]
	do
		set +e # Non zero exit expected
		ping -q -c1 -W1 "$IP_ADDRESS" > /dev/null 2>&1
		p=$?
		set -e
		if [ "$VERBOSE" -eq 1 ] ; then
			echo "[DEBUG]  Sending ping $i"
		fi
		i=$(($i+1))
	done

	if [ $p -ne 0 ] ; then
		echo "[ERROR]  Timeout : $IP_ADDRESS is unreachable."
		exit 1
	else
		if [ "$VERBOSE" -eq 1 ] ; then
			echo "[DEBUG]  $IP_ADDRESS is up."
		fi
	fi
}


VERBOSE=0
WAIT_UP=0
CREDENTIALS=""


set +o nounset

if [ -z "$1" ] ; then usage ; fi
while getopts 'hvwf:d:i:c:' OPTION; do
	case "$OPTION" in
		v) VERBOSE=1;;
		w) WAIT_UP=1 ;;
		d) OUTPUT_DIR="$OPTARG" ;;
                f) FILEPREFIX="$OPTARG" ;;
		c) CREDENTIALS="$OPTARG" ;;
		i) IP_ADDRESS="$OPTARG" ;;
		?|h) usage ;;
	esac
done
# shift $OPTIND -1

if [ "$VERBOSE" -eq 1 ] ; then
	echo "[DEBUG]  (Verbose Mode On)" 
	echo "[DEBUG]  OUTPUT_DIR provided : $OUTPUT_DIR" 
	echo "[DEBUG]  FILEPREFIX provided : $FILEPREFIX" 
	echo "[DEBUG]  IP_ADDRESS provided : $IP_ADDRESS"
	echo "[DEBUG]  CREDENTIALS provided : $CREDENTIALS"
	echo "[DEBUG]  WAIT_UP provided : $WAIT_UP"
fi

# No IP : error
if [ -z "$IP_ADDRESS" ] ; then usage ; fi

# Add @ to credentials if setted
if [ ! -z "$CREDENTIALS" ] ; then
	CREDENTIALS="$CREDENTIALS@"
fi

# Output dir Parser
if [ -z "$OUTPUT_DIR" ] ; then 
	OUTPUT_DIR=$(pwd)
else
	OUTPUT_DIR=$(readlink -m "$OUTPUT_DIR")
fi

if [ $VERBOSE -eq 1 ] ; then
	echo "[DEBUG]  OUTPUT_DIR : $OUTPUT_DIR" 
fi

# FILEPREFIX Parser
if [ -z "$FILEPREFIX" ] ; then
        FILEPREFIX=""
fi

if [ $WAIT_UP -eq 1 ] ; then
	wait_up
fi

take_picture

set -o nounset

exit 0

