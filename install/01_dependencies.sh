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

user=$(logname)

# echo "user is $user"
# echo "USER is $USER"
# echo "SUDO-USER is $SUDO_USER"

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedesktop.org distribution?"
	exit 1
fi
	
if [ "$ID"  == "debian" ]; then
	sudo apt install python3-pip tk make gcc python3-tk rsync python3-pysolar python3-crcmod python3-serial python3-matplotlib pipx net-tools ffmpeg sshfs
    [ ! -e /usr/bin/python ] && ln -s /usr/bin/python3 /usr/bin/python

elif [ "$ID"  == "manjaro" ]; then
	sudo pacman -Sy python-pip tk make gcc python-pipx python-crcmod python-pyserial python-matplotlib net-tools

	sudo -u $user python -m pip install pysolar --break-system-packages
fi
	
sudo -u $user python -m pipx install pyftdi
sudo -u $user python -m pip install yoctopuce --break-system-packages
