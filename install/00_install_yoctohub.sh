#!/usr/bin/bash

set -o nounset
set -euo pipefail

function usage(){
	printf "Usage sudo %s [-nv][-h] :\n" "$0"
	printf "  -v  Verbose Mode.\n"
	printf "  -n  Specify VirtualHub version.\n"
	printf "  -h, --help  Diplay this help message.\n"
	exit 1
}

if [[ $EUID -ne 0 ]]; then
	usage ;
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

VERBOSE=0
VERSION=0

if [ -z "${1-0}" ] ; then usage ; fi
while getopts 'hvn:' OPTION; do
	case "$OPTION" in
		v) VERBOSE=1;;
		n) VERSION="$OPTARG" ;;
		?|h) usage ;;
	esac
done

if [ "$VERBOSE" -eq 1 ] ; then
	echo "(Verbose Mode On)" 
	echo "VERSION provided : $VERSION" 
fi

if [ "$VERSION" -eq 0 ] ; then 
	output=$(wget https://www.yoctopuce.com/FR/common/getLastFirmwareLink.php -O -)
	VERSION=$(echo $output | cut -d',' -f1 | cut -d':' -f2)
	echo "Last version found on www.yoctopuce.com : $VERSION"
fi
last_virtualhub="VirtualHub.linux.$VERSION.zip"
virtualhub_link="http://www.yoctopuce.com/FR/downloads/$last_virtualhub"

cd /tmp
wget "$virtualhub_link" # Script will stop here if E404 is raised

mkdir Yoctopuce
unzip "$last_virtualhub" -d Yoctopuce/

# udev rules :
sudo cp Yoctopuce/udev_conf/51-yoctopuce_all.rules /etc/udev/rules.d/

# - 1: copy VitualHub binary to /usr/sbin
cp Yoctopuce/64bits/VirtualHub /usr/sbin

# - 2: ensure that the /usr/sbin/Virtualhub
chmod +x /usr/sbin/VirtualHub
rm -rf Yoctopuce "$last_virtualhub"

echo
echo "---------------------------------------------------------------"
echo "Try to run the VirtualHub with /usr/sbin/VirtualHub"
echo "and go to this webpage : 10.42.0.1:4444"

# Note previous used version of VirtualHub : 40924

# No need Systemd installation as we use it only once
# cp Yoctopuce/startup_script/yvirtualhub.service /etc/systemd/system/
# systemctl daemon-reload
# systemctl start yvirtualhub.service
# systemctl enable yvirtualhub.service
