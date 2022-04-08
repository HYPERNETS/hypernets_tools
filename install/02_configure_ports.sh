#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

source utils/configparser.sh

pantiltPort=$(parse_config "pantilt_port" config_dynamic.ini)

if [[ -z $pantiltPort ]] ; then
	pantiltPort="/dev/ttyS3"  # default value
fi



### helper script for finding next available device number
cat > /usr/local/sbin/unique-num << EOF
#!/bin/bash

if [ \$# -ne 3 ]; then
    echo "Usage: \$0 location prefix var-name" >&2
    exit 1
fi

location="\$1"
prefix="\$2"
key="\$3"

needindex=1
index=0

while [ \$needindex -eq 1 ]
do
        if [ ! -e \$location/\$prefix\$index ]; then
                needindex=0
                echo "\$key=\$index"
        else
                (( index++ ))
        fi
done

EOF

chmod 755 /usr/local/sbin/unique-num


### UDEV RULES:

## install rules
cat > /etc/udev/rules.d/90-hypstar-ports.rules << EOF
# udev rules to configure serial ports required for hypstar

# link ftdi to /dev/radiometer*, allow rw access
KERNEL=="ttyUSB*", SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", IMPORT{program}="/usr/local/sbin/unique-num /dev radiometer RADIOMETER_NUM", MODE="0666", SYMLINK+="radiometer%E{RADIOMETER_NUM}"

# allow rw access to pan-tilt port
KERNEL=="$pantiltPort", SUBSYSTEM=="tty", MODE="0666"

EOF

## cleanup, reload and trigger
rm -rf /dev/radiometer*
udevadm control --reload-rules
udevadm trigger
sleep 1
set +e
ls -l /dev/radiometer*
set -e
