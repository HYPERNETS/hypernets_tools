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
	sudo apt install python3-pip tk make gcc python3-tk rsync python3-pysolar python3-crcmod python3-serial python3-matplotlib python3-geopy python3-libgpiod net-tools ffmpeg sshfs python3-pyudev

	# pipx is not available on older Debian releases
	if [[ $(apt-cache search -n -q -q pipx | wc -l) -eq 0 ]]; then
		sudo -u $user python -m pip install pyftdi
	else
		sudo apt install pipx
		sudo -u $user python -m pipx install pyftdi
	fi

    [ ! -e /usr/bin/python ] && ln -s /usr/bin/python3 /usr/bin/python

	#  gpio_f7188x module is not compiled out of the box on Debian 11
	if ! modprobe --dry-run gpio_f7188x ; then
		apt install build-essential dkms linux-source linux-headers-amd64 libssl-dev libelf-dev
		pushd /usr/src
		kernel_ver=$(uname -r | cut -d . -f -2)
		tar axf linux-source-$kernel_ver.tar.xz

		# make sure the link is to the current running kernel headers
		rm -f /usr/src/linux
		ln -s /usr/src/linux-headers-$(uname -r) /usr/src/linux

		cd linux-source-$kernel_ver
		cp -f /boot/config-$(uname -r) .config
		sed -i.bak -e's/.*CONFIG_GPIO_F7188X.*/CONFIG_GPIO_F7188X=m/' .config
		cp -f ../linux/Module.symvers vmlinux.symvers
		make drivers/gpio/gpio-f7188x.ko
		cp -f drivers/gpio/gpio-f7188x.ko /lib/modules/$(uname -r)/kernel/drivers/gpio/
		depmod -a
		popd
	fi

elif [ "$ID"  == "manjaro" ]; then
	sudo pacman -Sy python-pip tk make gcc python-pipx python-crcmod python-pyserial python-matplotlib python-geopy libgpiod net-tools python-pyudev 

	sudo -u $user python -m pip install pysolar
	sudo -u $user python -m pipx install pyftdi
fi
	
sudo -u $user python -m pip install yoctopuce
