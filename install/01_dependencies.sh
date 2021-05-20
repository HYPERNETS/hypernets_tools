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

sudo pacman -Sy python-pip tk make gcc

sudo -u $user python -m pip uninstall serial
sudo -u $user python -m pip install crcmod pyftdi yoctopuce pyserial
sudo -u $user python -m pip install matplotlib

# Get Access to  /dev/ttySx without 'sudo'
sudo usermod -a -G uucp $USER


cd hypernets/libhypstar/
sudo -u $user make lib
sudo make install
cd -

# Ensure relogin
# reboot
