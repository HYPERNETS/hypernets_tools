#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

# TODO : Check last version before
last_version_yocto="VirtualHub.linux.40924.zip"

cd /tmp
wget "http://www.yoctopuce.com/FR/downloads/$last_version_yocto"
mkdir Yoctopuce
unzip $last_version_yocto -d Yoctopuce/

# udev rules :
sudo cp Yoctopuce/udev_conf/51-yoctopuce_all.rules /etc/udev/rules.d/

# - 1: copy VitualHub binary to /usr/sbin
cp Yoctopuce/64bits/VirtualHub /usr/sbin

# - 2: ensure that the /usr/sbin/Virtualhub
chmod +x /usr/sbin/VirtualHub

rm -rf Yoctopuce "$last_version_yocto"

echo
echo "---------------------------------------------------------------"
echo "Try to run the virtual hub with /usr/sbin/VirtualHub"
echo "and go to this webpage : 10.42.0.1:4444"

# - BYPASS  Systemd installation
# cp Yoctopuce/startup_script/yvirtualhub.service /etc/systemd/system/
# systemctl daemon-reload
# systemctl start yvirtualhub.service
# systemctl enable yvirtualhub.service
# reboot
