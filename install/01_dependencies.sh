#!/usr/bin/bash

set -o nounset
set -euo pipefail

XHL=$(tput setaf 9) ## red
RESET_HL=$(tput sgr0) ## reset all text formatting

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

PIP_BREAK_SYSTEM_PACKAGES=1

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedesktop.org distribution?"
	exit 1
fi
	
if [ "$ID" != "debian" ] && [ "$ID" != "manjaro" ]; then
	echo "${XHL}Error: only Debian and Manjaro are supported distributions${RESET_HL}"
	exit 1
fi

if [ "$ID"  == "debian" ]; then
	# Delete manually created symlink if it exists. It will be replaced by python-is-python3 package
	[ -e /usr/bin/python ] && [ $(dpkg-query -S /usr/bin/python > /dev/null 2>&1 ; echo $?) -eq 1 ] && rm -f /usr/bin/python

	sudo apt install python3-pip tk make gcc python3-tk rsync python3-pysolar python3-crcmod \
			python3-serial python3-matplotlib python3-geopy net-tools ffmpeg sshfs python3-pyudev \
			python-is-python3

	# pipx is not available on older Debian releases
	if [[ $(apt-cache search -n -q -q pipx | wc -l) -eq 0 ]]; then
		sudo -u $user python -m pip install pyftdi
		sudo -u $user python -m pip install yoctopuce
	else
		sudo apt install pipx
		sudo -u $user python -m pipx install pyftdi
		sudo -u $user python -m pip install yoctopuce --break-system-packages
	fi

elif [ "$ID"  == "manjaro" ]; then
	# store manjaro version
	if [ -f /etc/lsb-release ]; then
		source /etc/lsb-release
		old_os_ver="${DISTRIB_RELEASE:-}"
	fi

	sudo pacman -Syu python python-pip tk make gcc python-pipx python-crcmod python-pyserial \
			python-matplotlib python-geopy net-tools python-pyudev python-pyftdi gnu-netcat

	sudo -u $user python -m pip install pysolar --break-system-packages
	sudo -u $user python -m pip install yoctopuce --break-system-packages

	# warn if new OS version
	if [ -f /etc/lsb-release ]; then
		source /etc/lsb-release

		if [[ "${DISTRIB_RELEASE:-}" != "" ]] && [[ "${old_os_ver:-}" != "${DISTRIB_RELEASE:-}" ]]; then
			echo -e "\n----------------------------------------------------\n"
			echo -e "WARNING!!!!\n"
			echo "Manjaro has been upgraded from version '${old_os_ver:-}' to '${DISTRIB_RELEASE:-}'"
			echo -e "You should re-install libhypstar and rain sensor\n"
		fi
	fi
fi

