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
path_to_service=$(echo "$PWD/utils/run_service.sh" | sed 's/\//\\\//g')
path_to_h_tools=$(echo "$PWD" | sed 's/\//\\\//g')
service_file="/etc/systemd/system/hypernets-sequence.service"

cp "./install/hypernets-sequence.service" $service_file

sed -i '/User=$/s/$/'$user'/' $service_file
sed -i '/ExecStart=$/s/$/'$path_to_service'/' $service_file
sed -i '/WorkingDirectory=$/s/$/'$path_to_h_tools'\//' $service_file

systemctl enable hypernets-sequence
