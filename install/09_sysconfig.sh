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

if [ "$ID" != "debian" ] && [ "$ID" != "manjaro" ]; then
	echo "${XHL}Error: only Debian and Manjaro are supported distributions${RESET_HL}"
	exit 1
fi

user=$(logname)

## uninstall unnecessary large packages
set +e
if [ "$ID" == "debian" ]; then
	echo
	echo "${HL}Uninstalling needless large packages${RESET_HL}"
	apt purge libreoffice* gimp-data
	apt autoremove
elif [ "$ID" == "manjaro" ]; then
	echo
	echo "${HL}Uninstalling needless large packages${RESET_HL}"
	pacman -D --asdeps thunderbird android-tools 2> /dev/null
	pacman -D --asexplicit gcc
	pacman -Rns $(pacman -Qqtd)
fi
set -e

set +e
## disable services
if [ "$ID" == "debian" ]; then
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


# allow users to set clock
echo
echo "${HL}Allowing users to adjust PC clock${RESET_HL}"

# check polkit version
polkit_version=$(pkaction --version | sed -e 's/[^0-9]*//')
if (( $(echo "$polkit_version < 0.106" | bc -l) )); then
	# old polkit doesn't support Javascript syntax
	cat > /etc/polkit-1/localauthority/50-local.d/com.hypstar.timedate.pkla << EOF
[Allow $user set PC clock]
Identity=unix-user:$user
Action=org.freedesktop.timedate1.set-time
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF

else
	# new polkit supports Javascript syntax
	cat > /etc/polkit-1/rules.d/10-timedate.rules << EOF
polkit.addRule(function(action, subject) {
	if (action.id == "org.freedesktop.timedate1.set-time") {
		return polkit.Result.YES;
	}
});
EOF

fi

systemctl restart polkit.service

# set system clock to UTC
echo
echo "${HL}Setting system clock to UTC time zone${RESET_HL}"
timedatectl set-timezone UTC

# enable ntpd
echo
echo "${HL}Enabling systemd-timesyncd.service${RESET_HL}"
systemctl enable systemd-timesyncd.service
systemctl start systemd-timesyncd.service

# limit journal size to 1 GB
echo
echo "${HL}Limiting journal size to 1GB${RESET_HL}"
sed -i '/^SystemMaxUse=/d' /etc/systemd/journald.conf
echo "SystemMaxUse=1G" >> /etc/systemd/journald.conf


# add user to groups
if [ "$ID" == "debian" ]; then
	group_array=("sudo" "systemd-journal")
elif [ "$ID" == "manjaro" ]; then
	group_array=("wheel" "systemd-journal")
fi

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


## Workaround for debian bug where occasionally the gsm modem interface has wwx* name with x being random mac address
if [[ $(vnstat --dbiflist 1 | grep -c -e wwa -e wwp) -eq 0 ]] && [[ $(vnstat --iflist 1 | grep -c -e wwa -e wwp) -ne 0 ]]; then
	readarray -t iflist < <(vnstat --iflist 1)
	for interface in "${iflist[@]}"; do
		if [[ $interface =~ ^wwa ]] || [[ $interface =~ ^wwp ]]; then
			vnstat --add $interface
		fi
	done
fi
