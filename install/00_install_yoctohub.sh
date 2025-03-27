#!/usr/bin/bash

set -o nounset
set -euo pipefail

XHL=$(tput setaf 9) ## red
RESET_HL=$(tput sgr0) ## reset all text formatting

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
	echo "Not a systemd freedesktop.org distribution?"
	exit 1
fi

if [ "$ID" != "debian" ] && [ "$ID" != "manjaro" ]; then
	echo "${XHL}Error: only Debian and Manjaro are supported distributions${RESET_HL}"
	exit 1
fi

if [ ! "$ID"  == "debian" ]; then
	echo "Linux distribution not supported."
	echo "Please manually install the Yoctopuce virtualhub"
	echo "https://www.yoctopuce.com/EN/virtualhub.php"
	echo
	echo "and Yoctopuce command line API"
	echo "https://www.yoctopuce.com/EN/libraries.php"
	echo "Download linux intel and copy the contents of Binaries/linux/64bits/"
	echo "into ~/.local/bin/"
	exit 1
fi

wget -q -O - https://www.yoctopuce.com/apt/KEY.gpg | gpg --dearmor | sudo tee -a /usr/share/keyrings/yoctopuce.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/yoctopuce.gpg] https://www.yoctopuce.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/yoctopuce.list

sudo apt update
sudo apt install virtualhub
sudo apt install yoctolib-cmdlines

set +e
if [[ $(systemctl list-units --full -all | grep -F "yvirtualhub.service") ]]; then
	echo
	echo "Stop existing Virtualhub service"
	systemctl stop yvirtualhub.service
	systemctl disable yvirtualhub.service
fi
set -e

echo 
echo "Creating udev rules for all users.."

cat > /etc/udev/rules.d/51-yoctopuce_all.rules << EOF
# udev rules to allow write access to all users for Yoctopuce USB devices
SUBSYSTEM=="usb", ATTR{idVendor}=="24e0", MODE="0666"
EOF

echo 
echo "Creating systemd startup script..."

cat > /etc/systemd/system/yvirtualhub.service  << EOF
[Unit]
Description=Yoctopuce VirtualHub
After=network.target

[Service]
ExecStart=/usr/sbin/VirtualHub -c /etc/vhub.byn -n 127.0.0.1
Type=simple

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start yvirtualhub.service
systemctl enable yvirtualhub.service

echo
echo "Installation  VirtualHub done."
echo "---------------------------------------------------------------"
