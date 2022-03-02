#!/bin/bash

set -o nounset
set -euo pipefail


# Bash menu script for hypernets_tools installation.
echo 
echo "  _   _                                  _"
echo " | | | |_   _ _ __   ___ _ __ _ __   ___| |_ ___"
echo " | |_| | | | | '_ \ / _ \ '__| '_ \ / _ \ __/ __|"
echo " |  _  | |_| | |_) |  __/ |  | | | |  __/ |_\__ \ "
echo " |_| |_|\__, | .__/ \___|_|  |_| |_|\___|\__|___/"
echo "        |___/|_|"
echo 
echo "This script aims to help hypernets_tools installation"
echo "(Yoctopuce USB mode only)"
echo 


function check_sudo_user(){
	if [[ $EUID -ne 0 ]]; then
		echo "This script must be run as root, use sudo $0 instead"
		exit 1
	fi
}


function check_if_online(){
	set +e
	nm-online
	if [ $? -ne 0 ]; then
		echo "Error : please connect to internet."
		exit 1
	fi
	set -e
}


function download_repo(){
	# if [ -d "hypernets_tools" ]; then
	# 	echo "The hypernets_tools already folder exists."
	# 	exit 1
	# fi

	echo 
	echo 
	# echo "Step 1 -- Download and Update Hypernets Tools..."
	echo "------------------------------------------------"
	# sudo -u $SUDO_USER git clone https://github.com/hypernets/hypernets_tools 
	sudo -u $SUDO_USER git checkout beta
	sudo -u $SUDO_USER git pull
}


function download_yoctohub(){
	echo 
	echo 
	echo "Step 2 -- Download and Install the Yoctohub..."
	echo "------------------------------------------------"
	sudo ./install/00_install_yoctohub.sh
}

function auto_config_yocto(){
	echo "Copying configuration files"
	sudo -u $SUDO_USER cp hypernets/resources/config_static.ini.template config_static.ini
	sudo -u $SUDO_USER cp hypernets/resources/config_dynamic.ini.template config_dynamic.ini

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

	sudo -u $SUDO_USER sed -i -e '/OBSVLFR1/s/XXXXXX/'${yocto_id1:9:6}'/' config_static.ini
	sudo -u $SUDO_USER sed -i -e '/OBSVLFR2/s/XXXXXX/'${yocto_id2:9:6}'/' config_static.ini
	sudo -u $SUDO_USER sed -i -e '/YGNSSMK2/s/XXXXXX/'${yocto_gps:9:6}'/' config_static.ini
}

function install_dependencies(){
	echo 
	echo 
	echo "Step 3 -- Installation of python dependencies..."
	echo "------------------------------------------------"
	sudo -u $SUDO_USER ./install/01_dependencies.sh
}

function configure_port(){
	echo 
	echo 
	echo "Step 4 -- Configuration of the Hypstar Port..."
	echo "------------------------------------------------"
	sudo ./install/02_configure_ports.sh
}

function main_menu(){

	PS3='Please select an option:'
	options=(
		"Update hypernets_tools"
		"Download and install YoctoHub" 
 		"Run Yocto-Pictor auto-configuration"
 		"Install Dependencies"
		"Configure Hypstar Port"
 		"Quit")

	select opt in "${options[@]}"
	do
		case $opt in 
			"${options[0]}")
				check_if_online
				download_repo
				;;
			"${options[1]}")
				check_if_online
				download_yoctohub
				;;
			"${options[2]}")
				auto_config_yocto
				;;
			"${options[3]}")
				check_if_online
				install_dependencies
				;;
			"${options[4]}")
				echo "Not implemented!"
				;;
				*) echo "Invalid choice!"
		esac
	done
}

check_sudo_user
main_menu
# install_dependencies


echo 
echo 
echo "Step 5 -- Downloading and installing libhypstar..."
echo "------------------------------------------------"
# sudo ./install/03_update_libhypstar.sh 

echo 
echo 
echo "Installation Complete !"
