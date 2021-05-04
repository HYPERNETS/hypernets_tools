#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

## set time zone to UTC
timedatectl set-timezone UTC

## enable and start services
systemctl enable ntpdate.service
systemctl enable ntpd.service

systemctl start ntpdate.service
systemctl start ntpd.service
