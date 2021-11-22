#!/bin/bash

set -o nounset
set -euo pipefail

# Bash menu script for hypernets_tools installation.
echo 
echo "This script aims to help hypernets_tools installation"
echo "(Yoctopuce USB mode only)"
echo 

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

user="$SUDO_USER"

if [ -d "hypernets_tools" ]; then
	echo "The hypernets_tools folder exists."
	exit 1
fi

set +e
nm-online
if [ $? -ne 0 ]; then
	echo "Error : please connect to internet."
	exit 1
fi
set +e

echo 
echo 
echo "Step 1 -- Download and Update Hypernets Tools..."
echo "------------------------------------------------"
sudo -u $user git clone https://github.com/hypernets/hypernets_tools 
cd hypernets_tools/
sudo -u $user git checkout beta

echo 
echo 
echo "Step 2 -- Download and Install the Yoctohub..."
echo "------------------------------------------------"
sudo ./install/00_install_yoctohub.sh

echo "Copying configuration files"
sudo -u $user cp hypernets/resources/config_static.ini.template config_static.ini
sudo -u $user cp hypernets/resources/config_dynamic.ini.template config_dynamic.ini

echo 
echo 
echo "Running auto config for config_static.ini..."

json_api=$(wget -O- http://127.0.0.1:4444/api.json 2> /dev/null)

yocto_id2=$(echo $json_api | python3 -c \
	"import sys, json;
print(json.load(sys.stdin)['services']['whitePages'][1]['serialNumber'])")

yocto_gps=$(echo $json_api | python3 -c \
	"import sys, json;
print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][0]['logicalName'])")

yocto_id1=$(echo $json_api | python3 -c \
	"import sys, json;
print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][1]['logicalName'])")


echo 
echo 
echo "Yocto IDs are : $yocto_id1, $yocto_id2 and $yocto_gps" 

sudo -u $user sed -i -e '/OBSVLFR1/s/XXXXXX/'${yocto_id1:9:6}'/' config_static.ini
sudo -u $user sed -i -e '/OBSVLFR2/s/XXXXXX/'${yocto_id2:9:6}'/' config_static.ini
sudo -u $user sed -i -e '/YGNSSMK2/s/XXXXXX/'${yocto_gps:9:6}'/' config_static.ini

echo 
echo 
echo "Step 3 -- Installation of python dependencies..."
echo "------------------------------------------------"
sudo -u $user ./install/01_dependencies.sh

echo 
echo 
echo "Step 4 -- Configuration of the Hypstar Port..."
echo "------------------------------------------------"
sudo ./install/02_configure_ports.sh

echo 
echo 
echo "Step 5 -- Downloading and installing libhypstar..."
echo "------------------------------------------------"
sudo ./install/03_update_libhypstar.sh 

echo 
echo 
echo "Installation Complete !"
