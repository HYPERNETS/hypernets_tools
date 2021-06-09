#!/usr/bin/bash
# Usage: sudo ./00_install_yoctohub.sh $1
# with $1 version number (from https://www.yoctopuce.com/EN/virtualhub.php)

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

# TODO : Check last version before
version=${1:-$(echo 40924)}
last_version_yocto="VirtualHub.linux.$version.zip"
echo "Version to be installed: $last_version_yocto"

cd /tmp
wget "http://www.yoctopuce.com/FR/downloads/$last_version_yocto"
mkdir -p Yoctopuce
unzip $last_version_yocto -d Yoctopuce/

# udev rules :
sudo cp Yoctopuce/udev_conf/51-yoctopuce_all.rules /etc/udev/rules.d/

# - 1: copy VitualHub binary to /usr/sbin
cp -f Yoctopuce/64bits/VirtualHub /usr/sbin

# - 2: ensure that the /usr/sbin/Virtualhub
chmod +x /usr/sbin/VirtualHub

rm -rf Yoctopuce "$last_version_yocto"

echo
echo "---------------------------------------------------------------"
echo "Restart PC and then try to run the virtual hub with /usr/sbin/VirtualHub"
echo "and go to this webpage : 10.42.0.1:4444"

# - BYPASS  Systemd installation
# cp Yoctopuce/startup_script/yvirtualhub.service /etc/systemd/system/
# systemctl daemon-reload
# systemctl start yvirtualhub.service
# systemctl enable yvirtualhub.service
# reboot
