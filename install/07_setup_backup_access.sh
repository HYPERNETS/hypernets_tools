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

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedestkop.org distribution?"
	exit 1
fi

source utils/configparser.sh

sshIf=$(parse_config "backup_ssh_interface" config_static.ini)
sshIp=$(parse_config "backup_ssh_ip" config_static.ini)

if [ -z $sshIf ]; then
	sshIf="enp2s0"
fi

if [ -z $sshIp ]; then
	sshIp="192.168.123.123"
fi

echo "Read from config_static.ini : "
echo " * Backup SSH access interface : $sshIf"
echo " * Backup SSH access port      : $sshIp"
read -p "   Confirm (y/n) ?" -rn1
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then 
	echo

	## configure network interface
	cat << EOF > /etc/network/interfaces.d/ssh_backup_interface
auto $sshIf
iface $sshIf inet static
	address $sshIp/24
EOF

	systemctl restart networking


	## Set up ssh server
	apt install openssh-server

	cat << EOF > /etc/ssh/sshd_config.d/ssh_backup_sshd_config.conf
ListenAddress $sshIp
EOF

	if [ "$ID"  == "debian" ]; then
		systemctl enable ssh
		systemctl start ssh
	elif [ "$ID"  == "manjaro" ]; then
		systemctl enable sshd
		systemctl start sshd
	fi

else
	echo "Exit"
	exit 1
fi
