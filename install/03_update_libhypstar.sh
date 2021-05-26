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


# Init
sudo -u $user git submodule init
sudo -u $user git submodule update

# Update and Install
cd hypernets/scripts/libhypstar/
sudo -u $user git checkout main
sudo -u $user git pull
sudo -u $user make lib
sudo make install
cd -
