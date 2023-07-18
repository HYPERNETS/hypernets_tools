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
	echo "${XHL}This script must be run as root, use sudo $0 instead${RESET_HL}" 1>&2
	exit 1
fi

# if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
# 	echo "${XHL}This script must be run from hypernets_tools folder" 1>&2
# 	echo "Use : sudo ./install/${0##*/} instead${RESET_HL}"
# 	exit 1
# fi

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "${XHL}Error: impossible to detect OS system version."
	echo "Not a systemd freedesktop.org distribution?${RESET_HL}"
	exit 1
fi

user=$(logname)

## uninstall unnecessary large packages
echo
echo "${HL}Uninstalling needless large packages${RESET_HL}"
apt purge libreoffice* gimp-data
apt autoremove

set +e
## disable services
if [ "$ID"  == "debian" ]; then
	service_array=("bluetooth.service" "unattended-upgrades.service" "apt-daily.service" "apt-daily.timer" "apt-daily-upgrade.service" "apt-daily-upgrade.timer" "colord.service" "cups-browsed.service" "cups.service")

	for srv in "${service_array[@]}"
	do
			if [[ $(systemctl list-units --full -all | grep "$srv") ]]; then
			echo
			echo "${HL}Stopping and disabling $srv${RESET_HL}"
			systemctl stop "$srv"
			systemctl disable "$srv"
		fi
	done
fi
set -e


# set system clock to UTC
echo
echo "${HL}Setting system clock to UTC time zone${RESET_HL}"
timedatectl set-timezone UTC


# limit journal size to 1 GB
echo
echo "${HL}Limiting journal size to 1GB${RESET_HL}"
sed -i '/^SystemMaxUse=/d' /etc/systemd/journald.conf
echo "SystemMaxUse=1G" >> /etc/systemd/journald.conf


# add user to groups
group_array=("sudo" "systemd-journal")

echo
added_groups=0
for grp in "${group_array[@]}"
do
	if [[ ! $(groups "$user" | grep "$grp") ]]; then
		echo "${HL}Adding user $user to $grp group${RESET_HL}"
		/usr/sbin/usermod -aG "$grp" "$user"
		added_groups=1
	fi
done
if [[ "$added_groups" == 1 ]]; then echo -e "${XHL}\nLog out and back in for the change to take effect!${RESET_HL}"; fi

