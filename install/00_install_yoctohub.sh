#!/usr/bin/bash

set -o nounset
set -euo pipefail

function usage(){
	printf "Usage sudo %s [-nv][-h] :\n" "$0"
	printf "  -v  Verbose Mode.\n"
	printf "  -n  Specify VirtualHub version.\n"
	printf "  -h, --help  Diplay this help message.\n"
	exit 1
}

if [[ $EUID -ne 0 ]]; then
	usage ;
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

VERBOSE=0

if [ -z "${1-0}" ] ; then usage ; fi
while getopts 'hvn:' OPTION; do
	case "$OPTION" in
		v) VERBOSE=1;;
		?|h) usage ;;
	esac
done

if [ "$VERBOSE" -eq 1 ] ; then
	echo "(Verbose Mode On)" 
fi

wget -qO - https://www.yoctopuce.com/apt/KEY.gpg |  sudo apt-key add -
echo "deb https://www.yoctopuce.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/yoctopuce.list 
sudo apt update
sudo apt install virtualhub
