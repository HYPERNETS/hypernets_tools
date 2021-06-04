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
	printf "  -i, IP_ADDRESS   Specify the ip address of the camera.\n"
	printf "  -c, USER:PASS    Specify credentials camera.\n"
	printf "  -p, PREFIX       Prefix name of output images.\n"
	printf "  -h, --help       Diplay this help message.\n"
	printf " Note : default is current directory if not specified.\n"
	exit 0
}

function take_picture(){
	mkdir -p "$OUTPUT_DIR"
	DATE=$(date -u +"%Y%m%dT%H%M%S") 
	# touch $OUTPUT_DIR/$DATE.jpg
	ffmpeg -y -i rtsp://"$CREDENTIALS$IP_ADDRESS":554 -vframes 1 \
		"$OUTPUT_DIR/$PREFIX""_$DATE.jpg"
	if [ "$VERBOSE" -eq 1 ]; then
		echo Output File is : "$OUTPUT_DIR/$PREFIX""_$DATE.jpg"
	fi
}

function wait_up(){

	# Ping the camera until it starts
	# Timeout : 2 min 30 s
	timeout=150

	if [ "$VERBOSE" -eq 1 ] ; then
		echo Waiting for "$IP_ADDRESS"...
	fi

	p=1 ; i=1
	while [[ $p -ne 0 ]] && [[ $i -le $timeout ]]
	do
		set +e # Non zero exit expected
		ping -q -c1 -W1 -q "$IP_ADDRESS" > /dev/null 2>&1
		p=$?
		set -e
		if [ "$VERBOSE" -eq 1 ] ; then
			echo Sending ping $i
		fi
		i=$(($i+1))
	done

	if [ $p -ne 0 ] ; then
		if [ "$VERBOSE" -eq 1 ] ; then
			echo Timeout : "$IP_ADDRESS" is unreachable.
		fi	
		exit 1
	else
		if [ "$VERBOSE" -eq 1 ] ; then
			echo "$IP_ADDRESS" is up.
		fi
	fi
}


VERBOSE=0
WAIT_UP=0
CREDENTIALS=""

set +o nounset

if [ -z "$1" ] ; then usage ; fi
while getopts 'hvwd:i:p:c:' OPTION; do
	case "$OPTION" in
		v) VERBOSE=1;;
		w) WAIT_UP=1 ;;
		d) OUTPUT_DIR="$OPTARG" ;;
		c) CREDENTIALS="$OPTARG" ;;
		i) IP_ADDRESS="$OPTARG" ;;
		p) PREFIX="$OPTARG" ;;
		?|h) usage ;;
	esac
done
# shift $OPTIND -1

if [ "$VERBOSE" -eq 1 ] ; then
	echo "(Verbose Mode On)" 
	echo "OUTPUT_DIR provided : $OUTPUT_DIR" 
	echo "IP_ADDRESS provided : $IP_ADDRESS"
	echo "CREDENTIALS provided : $CREDENTIALS"
	echo "WAIT_UP provided : $WAIT_UP"
	echo "PREFIX provided : $PREFIX"
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
	OUTPUT_DIR=$(readlink -f "$OUTPUT_DIR")
fi

if [ $VERBOSE -eq 1 ] ; then
	echo "OUTPUT_DIR : $OUTPUT_DIR" 
fi

if [ $WAIT_UP -eq 1 ] ; then
	wait_up
fi

take_picture

set -o nounset

exit 0
