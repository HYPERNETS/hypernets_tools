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
	echo "Not a systemd freedesktop.org distribution?"
	exit 1
fi

source utils/configparser.sh

sshIf=$(parse_config "backup_ssh_interface" config_static.ini)
sshIp=$(parse_config "backup_ssh_ip" config_static.ini)
dhcpServer=$(parse_config "dhcp_server" config_static.ini)

if [ -z $sshIf ]; then
	sshIf="enp2s0"
fi

if [ -z $sshIp ]; then
	sshIp="192.168.123.123"
fi

echo "Read from config_static.ini : "
echo " * Backup SSH access interface  : $sshIf"
echo " * Backup SSH access IP address : $sshIp"
echo " * DHCP server                  : $dhcpServer"
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

	## Set up DHCP server
	if [[ $dhcpServer == "yes" ]]; then
		apt install isc-dhcp-server

		sed -i "/INTERFACESv4=/s/.*/INTERFACESv4=\"$sshIf\"/" /etc/default/isc-dhcp-server

		mv -f /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.bak
		subnet=$(awk -F "." '{print $1"."$2"."$3".0"}' <<< $sshIp)
		last_octet=$(sed -e 's/.*\.//' <<< $sshIp)

		if (( "$last_octet" < "100" )); then
			range1=$(awk -F "." '{print $1"."$2"."$3".200"}' <<< $sshIp)
			range2=$(awk -F "." '{print $1"."$2"."$3".250"}' <<< $sshIp)
		else
			range1=$(awk -F "." '{print $1"."$2"."$3".1"}' <<< $sshIp)
			range2=$(awk -F "." '{print $1"."$2"."$3".50"}' <<< $sshIp)
		fi

		cat << EOF > /etc/dhcp/dhcpd.conf
option domain-name-servers ns1.example.org, ns2.example.org;

default-lease-time 7200;
max-lease-time 86400;

ddns-update-style none;

subnet $subnet netmask 255.255.255.0 {
  range $range1 $range2;
}

EOF

		systemctl enable isc-dhcp-server
		systemctl start isc-dhcp-server
	elif [[ -f "/etc/default/isc-dhcp-server" ]]; then
		systemctl stop isc-dhcp-server
		systemctl disable isc-dhcp-server

		sed -i "/INTERFACESv4=/s/.*/INTERFACESv4=\"\"/" /etc/default/isc-dhcp-server
	fi
else
	echo "Exit"
	exit 1
fi
