#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : sudo ./install/${0##*/} instead"
	exit 1
fi

user="$SUDO_USER"


# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedestkop.org distribution?"
	exit 1
fi

if [ "$ID"  == "debian" ]; then
	sudo apt install python3-pip tk make gcc python3-tk
elif [ "$ID"  == "manjaro" ]; then
	sudo pacman -Sy python-pip tk make gcc
fi

sudo -u $user python3 -m pip uninstall serial
sudo -u $user python3 -m pip install crcmod pyftdi yoctopuce pyserial
sudo -u $user python3 -m pip install matplotlib

# Get Access to  /dev/ttySx without 'sudo'
sudo usermod -a -G uucp $USER


# Ensure relogin
# reboot
