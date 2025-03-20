#!/usr/bin/bash

set -o nounset
set -euo pipefail

## define text highlights
HL=$(tput setaf 12) ## blue
XHL=$(tput setaf 9) ## red
BOLD=$(tput bold)
GREEN=$(tput setaf 10)
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

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedesktop.org distribution?"
	exit
fi

if [ "$ID" != "debian" ] && [ "$ID" != "manjaro" ]; then
	echo "${XHL}Error: only Debian and Manjaro are supported distributions${RESET_HL}"
	exit
fi

source utils/configparser.sh

sshIf=$(parse_config "backup_ssh_interface" config_static.ini)
sshIp=$(parse_config "backup_ssh_ip" config_static.ini)
dhcpServer=$(parse_config "dhcp_server" config_static.ini)
poe_cameras=$(parse_config "poe_cameras" config_static.ini)

if [ -z $sshIf ] || [ -z $sshIp ] || [ -z $dhcpServer ]; then
	echo "${XHL}Please define backup_ssh_interface, backup_ssh_ip, and dhcp_server"
	echo "parameters in config_static.ini${RESET_HL}"
fi

echo "Read from config_static.ini : "
echo " * Backup SSH access interface  : $sshIf"
echo " * Backup SSH access IP address : $sshIp"
echo " * DHCP server                  : $dhcpServer"
read -p "   Confirm (y/n) ?" -rn1
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then 
	echo "${XHL}Exit${RESET_HL}"
	exit
fi

echo

## check if interface exists
if ! ip link show "$sshIf" > /dev/null 2>&1 ; then
	echo "${XHL}Interface $sshIf does not exist!${RESET_HL}"
	echo "Available interfaces are:"
	echo "$(ip -br link show | cut -d' ' -f 1 | grep -e "^enp" -e "^wlp")"
	echo "${XHL}Please modify 'backup_ssh_interface' in config_static.ini and rerun this script!${RESET_HL}"
	exit
fi


############ configure network interface
if [[ "$sshIf" =~ ^enp ]]; then ## ethernet

	## delete previous conf
	rm -rf /etc/network/interfaces.d/ssh_backup_interface

	read -p "Disable WiFi (y/n) ?" -rn1
	echo

	if [[ $REPLY =~ ^[Yy]$ ]]; then 
		nmcli radio wifi off
	fi

	if [[ $(nmcli connection show | grep ssh_backup_interface) ]]; then
		nmcli connection delete ssh_backup_interface
	fi

	## enp2s0 already configured for PoE cameras
	if [[ "$sshIf" == "enp2s0" ]] && [[ $(nmcli connection show | grep poe_cam_interface | grep enp2s0) ]] || [[ $(grep -s enp2s0 /etc/network/interfaces.d/poe_cam_interface) ]] ; then
		echo "${XHL}enp2s0 interface already configured for PoE cameras${RESET_HL}"
		
		## get IP from PoE config and warn if not the same as backup_ssh_ip in config
		if [ "$ID"  == "debian" ]; then
			poe_ip="$(grep address /etc/network/interfaces.d/poe_cam_interface | sed -e 's/.*address //;s/\/.*//')"
		elif [ "$ID"  == "manjaro" ]; then
			poe_ip="$(nmcli -g IP4 connection show poe_cam_interface | cut -d ":" -f 2 | sed -e 's/\/.*//')"
		fi

		if [[ "$poe_ip" != "$sshIp" ]]; then
			echo
			echo "${XHL}Warning!! Using $poe_ip from PoE camera configuration instead of backup_ssh_ip ($sshIp) from config_static.ini${RESET_HL}"
			echo "${XHL}Set backup_ssh_ip = $poe_ip in config_static.ini or reconfigure PoE cameras to avoid confusion${RESET_HL}"
			echo
			sshIp="$poe_ip"
		fi
	elif [ "$ID"  == "debian" ]; then
		cat << EOF > /etc/network/interfaces.d/ssh_backup_interface
auto $sshIf
iface $sshIf inet static
	address $sshIp/24
EOF
		systemctl restart networking.service
	elif [ "$ID"  == "manjaro" ]; then
		## configure network interface
		nmcli connection add type ethernet ifname $sshIf con-name ssh_backup_interface ip4 $sshIp/24 ipv4.method manual autoconnect yes
		nmcli connection up ssh_backup_interface
	fi
elif [[ "$sshIf" =~ ^wlp ]]; then ## wifi
	## read the wifi password
	while [ 1 ]; do
		read -p "${HL}Enter new password for the wifi hotspot: ${RESET_HL}" -sr
		wifi_pass=$REPLY
		echo
		if [[ ${#wifi_pass} -lt 8 ]]; then
			echo -e "${XHL}The password must contain at least 8 symbols!${RESET_HL}\n"
			continue
		fi

		read -p "${HL}Retype the password: ${RESET_HL}" -sr
		echo

		if [[ "$wifi_pass" != "$REPLY" ]]; then 
			echo -e "${XHL}The passwords did not match!${RESET_HL}\n"
		else
			unset REPLY
			break
		fi
	done

	## delete previous conf
	rm -rf /etc/network/interfaces.d/ssh_backup_interface
	if [[ $(nmcli connection show | grep ssh_backup_interface) ]]; then
		nmcli connection delete ssh_backup_interface
	fi

	## if ipv4.method is shared instead of manual the PC will share its internet connection over wifi
	nmcli connection add type wifi ifname $sshIf con-name ssh_backup_interface \
			autoconnect yes ssid HYPSTAR 802-11-wireless.mode ap 802-11-wireless.band bg \
			ip4 $sshIp/24 ipv4.method manual wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$wifi_pass" wifi.channel 7

	nmcli radio wifi on
    nmcli connection up ssh_backup_interface

	unset wifi_pass
else
	echo "${XHL}Invalid interface $sshIf${RESET_HL}"
	echo "Allowed values for backup_ssh_interface in config_static.ini are:"
	echo "$(ip -br link show | cut -d' ' -f 1 | grep -e "^enp" -e "^wlp")"
	echo "${XHL}Please modify 'backup_ssh_interface' in config_static.ini and rerun this script!${RESET_HL}"
	exit
fi


############### Set up ssh server
## listen only on the backup_ssh_ip and localhost interfaces and not on 0.0.0.0
if [ "$ID"  == "debian" ]; then
	apt install openssh-server

	systemctl stop ssh.service
	systemctl enable ssh.service
	systemctl start ssh.service
elif [ "$ID"  == "manjaro" ]; then
	systemctl stop sshd.service
	systemctl enable sshd.service
	systemctl start sshd.service
fi



######## Set up DHCP server ########
if [[ $dhcpServer == "yes" ]]; then
	subnet=$(awk -F "." '{print $1"."$2"."$3".0"}' <<< $sshIp)
	last_octet=$(sed -e 's/.*\.//' <<< $sshIp)

	if (( "$last_octet" < "100" )); then
		range1=$(awk -F "." '{print $1"."$2"."$3".200"}' <<< $sshIp)
		range2=$(awk -F "." '{print $1"."$2"."$3".250"}' <<< $sshIp)
	else
		range1=$(awk -F "." '{print $1"."$2"."$3".1"}' <<< $sshIp)
		range2=$(awk -F "." '{print $1"."$2"."$3".50"}' <<< $sshIp)
	fi

	if [ "$ID"  == "debian" ]; then
		apt install isc-dhcp-server

		sed -i "/INTERFACESv4=/s/.*/INTERFACESv4=\"$sshIf\"/" /etc/default/isc-dhcp-server

		mv -f /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.bak

		cat << EOF > /etc/dhcp/dhcpd.conf
default-lease-time 7200;
max-lease-time 86400;

ddns-update-style none;

subnet $subnet netmask 255.255.255.0 {
  range $range1 $range2;
}

EOF

		systemctl enable isc-dhcp-server.service
		systemctl start isc-dhcp-server.service
	elif [ "$ID"  == "manjaro" ]; then
		pacman -Sy dhcp

		mv -f /etc/dhcpd.conf /etc/dhcpd.conf.bak

		cat << EOF > /etc/dhcpd.conf
default-lease-time 7200;
max-lease-time 86400;

ddns-update-style none;

subnet $subnet netmask 255.255.255.0 {
  range $range1 $range2;
}

EOF
		systemctl enable dhcpd4.service
		systemctl start dhcpd4.service
		systemctl stop dhcpd6.service
		systemctl disable dhcpd6.service
	fi # manjaro
else # dhcp = no
	if [ "$ID"  == "debian" ]; then
		if [[ -f "/etc/default/isc-dhcp-server" ]]; then
			systemctl stop isc-dhcp-server.service
			systemctl disable isc-dhcp-server.service

			sed -i "/INTERFACESv4=/s/.*/INTERFACESv4=\"\"/" /etc/default/isc-dhcp-server
		fi
	elif [ "$ID"  == "manjaro" ]; then
		if [[ -f "/etc/dhcpd.conf" ]]; then
			systemctl stop dhcpd4.service
			systemctl disable dhcpd4.service
			systemctl stop dhcpd6.service
			systemctl disable dhcpd6.service
		fi
	fi # manjaro
fi # dhcp = yes / no
