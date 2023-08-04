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

# Detection of what system we are currently running (i.e. debian or manjaro)
if [ -f /etc/os-release ]; then
	source /etc/os-release
else
	echo "Error: impossible to detect OS system version."
	echo "Not a systemd freedesktop.org distribution?"
	exit 1
fi

if [ "$ID" != "debian" ] && [ "$ID" != "manjaro" ]; then
	echo "${XHL}Error: only Debian and Manjaro are supported distributions${RESET_HL}"
	exit 1
fi

source utils/configparser.sh

pantiltPort=$(parse_config "pantilt_port" config_dynamic.ini)

if [[ -z $pantiltPort ]] ; then
	pantiltPort="/dev/ttyS0"  # default value
fi

echo "Using port $pantiltPort for Pan-tilt."
echo "This should be normally /dev/ttyS3 for V1 & V2 systems and /dev/ttyS0 for V3"
echo 

pantiltPort=$(echo $pantiltPort | rev | cut -d'/' -f1 | rev)

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




# load GPIO chip kernel module
if [ "$ID"  == "debian" ]; then
	modules_file="/etc/modules"
elif [ "$ID"  == "manjaro" ]; then
	modules_file="/etc/modules-load.d/modules.conf"
fi

if [[ ! $(grep "^gpio_f7188x" "$modules_file") ]]; then
	echo "gpio_f7188x" >> "$modules_file"
fi

set +e
rmmod ftdi-sio > /dev/null 2>&1
modprobe gpio_f7188x
modprobe ftdi-sio
set -e

### UDEV RULES:

## install rules
cat > /etc/udev/rules.d/90-hypstar-ports.rules << EOF
# udev rules to configure serial ports required for hypstar

# link ftdi to /dev/radiometer*, allow rw access
KERNEL=="ttyUSB*", SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", IMPORT{program}="/usr/local/sbin/unique-num /dev radiometer RADIOMETER_NUM", MODE="0666", SYMLINK+="radiometer%E{RADIOMETER_NUM}"

# allow rw access to pan-tilt port
KERNEL=="$pantiltPort", SUBSYSTEM=="tty", MODE="0666"

# allow rw access to rain sensor gpio port through libgpiod
# we assume that gpio-f7188x is initialised before ftdi-cbus
# and gpio-f7188x-7 is gpiochip7
# The chip label has to be double-checked before using!
# The chip label is unfortunately not listed in udevadm info --attribute-walk /dev/gpiochip7
KERNEL=="gpiochip7", SUBSYSTEM=="gpio", DRIVERS=="gpio-f7188x", MODE="0666"

EOF

## cleanup, reload and trigger
udevadm control --reload-rules
rm -rf /dev/radiometer*
udevadm trigger
sleep 1
set +e
ls -l /dev/radiometer*
set -e
