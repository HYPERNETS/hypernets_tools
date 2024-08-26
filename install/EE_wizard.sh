#!/bin/bash

set -o nounset
set -euo pipefail


# Bash menu script for hypernets_tools installation.
function print_logo(){
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
}


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


function update_repo(){
	echo 
	echo 
	echo "-- Update Hypernets Tools..."
	echo "------------------------------------------------"
	sudo -u $SUDO_USER git pull
}


function download_yoctohub(){
	echo 
	echo 
	echo "-- Download and Install the Yoctohub..."
	echo "------------------------------------------------"
	sudo ./install/00_install_yoctohub.sh
}

function auto_config_yocto(){
	echo 
	echo 
	echo "-- Auto-config for YoctoPictor..."
	echo "------------------------------------------------"

	# if [[ -f "config_static.ini" ]] || [[ -f "config_dynamic.ini" ]]; then
	if [[ -f "config_static.ini" ]]; then
		echo "Error: configuration file found, please remove it first."
		return
	fi

	echo "Please connect the Yocto-Pictor from the 'config port' and press
    'enter' to continue"
	read

	echo "Copying configuration files"
	sudo -u $SUDO_USER cp hypernets/resources/config_static.ini.template config_static.ini

	if [[ ! -f "config_dynamic.ini" ]]; then
        echo "Copying the config_dynamic.ini file as it does not exist"
        sudo -u $SUDO_USER cp hypernets/resources/config_dynamic.ini.template config_dynamic.ini
    fi

	echo 
	echo "Running auto config for config_static.ini..."

	json_api=$(wget -O- http://127.0.0.1:4444/api.json 2> /dev/null)

	yocto_id2=$(echo $json_api | python3 -c \
		"import sys, json; print(json.load(sys.stdin)['services']['whitePages'][1]['serialNumber'])")

	yocto_gps=$(echo $json_api | python3 -c \
		"import sys, json; print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][0]['logicalName'])")

	yocto_id1=$(echo $json_api | python3 -c \
		"import sys, json; print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][1]['logicalName'])")

	echo "Yocto IDs are : $yocto_id1, $yocto_id2 and $yocto_gps" 

	sudo -u $SUDO_USER sed -i -e '/OBSVLFR1/s/XXXXXX/'${yocto_id1:9:6}'/' config_static.ini
	sudo -u $SUDO_USER sed -i -e '/OBSVLFR2/s/XXXXXX/'${yocto_id2:9:6}'/' config_static.ini
	sudo -u $SUDO_USER sed -i -e '/YGNSSMK2/s/XXXXXX/'${yocto_gps:9:6}'/' config_static.ini
}

function install_dependencies(){
	echo 
	echo 
	echo "-- Installation of python dependencies..."
	echo "------------------------------------------------"
	sudo ./install/01_dependencies.sh
}


function update_libhypstar(){
	echo 
	echo 
	echo "-- Downloading and installing libhypstar..."
	echo "------------------------------------------------"
    user="$SUDO_USER"

    # Init
    sudo -u $user git submodule init
    sudo -u $user git submodule update

    # Update and Install
    cd hypernets/hypstar/libhypstar/
    sudo -u $user git checkout oldmain
    sudo -u $user git pull
    sudo -u $user make clean lib
    sudo make install
    cd -
    # sudo ./install/03_update_libhypstar.sh 
}


function configure_port(){
    echo 
	echo 
	echo "-- Configuration of the Hypstar Port..."
	echo "------------------------------------------------"
	echo "Please connect the FTDI card and press enter to continue"
	read
	sudo ./install/02_configure_ports.sh
}


function main_menu(){
while true; do
	echo "------------------------------------------------"
	PS3='Please select an option:'
	options=(
		"Update hypernets_tools"
 		"Install Dependencies"
		"Download and install YoctoHub" 
 		"Run Yocto-Pictor auto-configuration"
		"Install / Update libhypstar"
		"Configure Hypstar Port"
		# "Check installation before field deployment"
 		"Quit")

	select opt in "${options[@]}"
	do
		case $opt in 
			"${options[0]}")
				check_if_online
				update_repo
				break
				;;
			"${options[1]}")
				check_if_online
				install_dependencies
				break
				;;
			"${options[2]}")
				check_if_online
				download_yoctohub
				break
				;;
			"${options[3]}")
				auto_config_yocto
				break
				;;
			"${options[4]}")
				check_if_online
				update_libhypstar
				break
				;;
			"${options[5]}")
				configure_port
				break
				;;
			"${options[6]}")
                exit 0
				break
				;;
			*)
				echo "Not implemented!"
				break
				;;
			*)
				echo "Invalid choice!"
				;;
		esac
	done
done
}

# TODO: error handler
print_logo
check_sudo_user
main_menu
