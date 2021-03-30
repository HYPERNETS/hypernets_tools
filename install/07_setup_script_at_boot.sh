#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : sudo ./install/${0##*/} instead"
	exit 1
fi

user="$SUDO_USER"
path_to_service="$PWD/run_service.sh"
path_to_h_tools="$PWD"

echo $user
echo $path_to_service
echo $path_to_h_tools

# systemctl enable hypernets.service
