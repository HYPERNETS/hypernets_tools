#!/usr/bin/bash

# USE WITH CAUTION : 
# see : https://github.com/HYPERNETS/hypernets_tools/pull/2#issuecomment-759553325


set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

## Install hostapd
pacman -Syu --noconfirm hostapd

## generate pseudo-random mac from actual wifi mac address
macaddr=$(ip addr show dev wlp12s0 | grep ether | awk '{print $2}')
newmacaddr=$(echo $macaddr | md5sum | sed 's/^\(..\)\(..\)\(..\)\(..\)\(..\).*$/02:\1:\2:\3:\4:\5/')

## generate service file
cat > /lib/systemd/system/wireless-interface.service << EOF
[Unit]
Description=Create additional wireless interface
BindsTo=sys-subsystem-net-devices-wlp12s0.device
After=sys-subsystem-net-devices-wlp12s0.device
Before=network.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/iw dev wlp12s0 interface add wlan0_infra type managed addr $newmacaddr

[Install]
WantedBy=multi-user.target

EOF

systemctl enable wireless-interface.service
systemctl start wireless-interface.service

