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
	## make a few different attempts to satisfy all distros
	if ! nc -zw1 google.com 443 > /dev/null 2>&1 && \
			! ping -q -c 1 -W 1 google.com > /dev/null 2>&1 && \
			! wget -q --spider http://google.com > /dev/null 2>&1
	then
		echo -e "\nError : please connect to internet.\n"
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
	./install/00_install_yoctohub.sh
}

function auto_config_yocto(){
	echo 
	echo 
	echo "-- Auto-config for YoctoPictor..."
	echo "------------------------------------------------"

	if [[ -f "config_static.ini" ]]; then
		echo "Error: config_static.ini file found, please remove it first."
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

	yocto_ver=$(echo $json_api | python3 -c \
		"import sys, json; print(json.load(sys.stdin)['services']['whitePages'][1]['productName'])")

	if [[ "$yocto_ver" == "Yocto-Pictor-Wifi" ]]; then
	# HYPSTAR host system V1-V3
		yocto_id2=$(echo $json_api | python3 -c \
			"import sys, json; print(json.load(sys.stdin)['services']['whitePages'][1]['serialNumber'])")

		yocto_gps=$(echo $json_api | python3 -c \
			"import sys, json; print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][0]['logicalName'])")

		yocto_id1=$(echo $json_api | python3 -c \
			"import sys, json; print(json.load(sys.stdin)['services']['yellowPages']['HubPort'][1]['logicalName'])")

		echo -e "\nFound host system V1-V3 using Yocto-Pictor-Wifi"
		echo "Yocto IDs are : $yocto_id1, $yocto_id2 and $yocto_gps" 

		sudo -u $SUDO_USER sed -i -e '/OBSVLFR1/s/XXXXXX/'${yocto_id1:9:6}'/' config_static.ini
		sudo -u $SUDO_USER sed -i -e '/OBSVLFR2/s/XXXXXX/'${yocto_id2:9:6}'/' config_static.ini
		sudo -u $SUDO_USER sed -i '/yocto_prefix3 [-=]/d' config_static.ini
		sudo -u $SUDO_USER sed -i -e '/YGNSSMK2/s/XXXXXX/'${yocto_gps:9:6}'/' config_static.ini
	elif [[ "$yocto_ver" == "Yocto-Pictor-GPS" ]]; then
	# HYPSTAR host system V4-...
		yocto_id3=$(echo $json_api | python3 -c \
			"import sys, json; print(json.load(sys.stdin)['services']['whitePages'][1]['serialNumber'])")

		yocto_id1=$(echo $json_api | python3 -c \
			"import sys, json; print(json.load(sys.stdin)['services']['whitePages'][2]['serialNumber'])")

		echo -e "\nFound host system V4 or newer using Yocto-Pictor-GPS"
		echo "Yocto IDs are : $yocto_id1 and $yocto_id3" 

		sudo -u $SUDO_USER sed -i -e '/OBSVLFR1/s/XXXXXX/'${yocto_id1:9:6}'/' config_static.ini
		sudo -u $SUDO_USER sed -i '/yocto_prefix2 [-=]/d' config_static.ini
		sudo -u $SUDO_USER sed -i -e '/OBSVLFR3/s/XXXXXX/'${yocto_id3:9:6}'/' config_static.ini
		sudo -u $SUDO_USER sed -i '/yocto_gps [-=]/d' config_static.ini

		echo
		echo "You should now edit the configuration files before continuing with the configuration."
		echo

	else
	# Something is wrong
		echo -e "\nError : failed to autodetect the Yocto boards.\n"
		exit 1
	fi
}

function install_dependencies(){
	echo 
	echo 
	echo "-- Installation of python dependencies..."
	echo "------------------------------------------------"
	./install/01_dependencies.sh
}


function update_libhypstar(){
	echo 
	echo 
	echo "-- Downloading and installing libhypstar..."
	echo "------------------------------------------------"
    ./install/03_update_libhypstar.sh 
}


function configure_port(){
    echo 
	echo 
	echo "-- Configuration of the Hypstar and pan-tilt ports..."
	echo "------------------------------------------------"
	./install/02_configure_ports.sh
}


function setup_backdoor(){
    echo 
	echo 
	echo "-- Seting up ssh server for backup access..."
	echo "------------------------------------------------"
	./install/07_setup_backup_access.sh
}


function setup_rain_sensor(){
    echo 
	echo 
	echo "-- Seting up rain sensor..."
	echo "------------------------------------------------"
	./install/FF_setup_rain_sensor.sh
}


function os_config(){
    echo 
	echo 
	echo "-- Optimising Operating System configuration..."
	echo "------------------------------------------------"
	./install/09_sysconfig.sh
}


function setup_services(){
    echo 
	echo 
	echo "-- Setting up Hypernets startup services..."
	echo "------------------------------------------------"
	echo 
	echo "Which service to configure?"
	echo "------------------------------------------------"
    PS3='Please select an option: '
    srv_options=(
		"Spectral measurements (hypernets-sequence.service)" # 1
		"Data synchronisation (hypernets-hello.service)" # 2
		"Reverse ssh (hypernets-access.service)" # 3
		"Webcams (hypernets-webcam.service)" # 4
		"All of the above" # 5
    )
	select opt in "${srv_options[@]}"
	do
		case $opt in 
			"${srv_options[0]}") # (hypernets-sequence.service) # 1
				./install/04_setup_script_at_boot.sh
				break
				;;
			"${srv_options[1]}") # (hypernets-hello.service) # 2
				./install/05_setup_server_communication.sh
				break
				;;
			"${srv_options[2]}") # (hypernets-access.service) # 3
				./install/06_setup_remote_access.sh
				break
				;;
			"${srv_options[3]}") # (hypernets-webcam.service) # 4
				./install/CC_setup_webcams.sh
				break
				;;
			"${srv_options[4]}") # "All of the above" # 5
				./install/04_setup_script_at_boot.sh
				./install/05_setup_server_communication.sh
				./install/06_setup_remote_access.sh
				./install/CC_setup_webcams.sh
				break
				;;
			*)
				echo -e "\nInvalid choice!\n"
				break
				;;
		esac
	done

}


function main_menu(){
while true; do
	echo
	echo "------------------------------------------------"
	PS3='Please select an option: '
	OPT1="Update hypernets_tools"
 	OPT2="Install dependencies"
	OPT3="Download and install YoctoHub"
 	OPT4="Run Yocto-Pictor auto-configuration"
	OPT5="Install / update libhypstar"
	OPT6="Configure ports"
	OPT7="Setup rain sensor"
	OPT8="Operating system configuration"
	OPT9="Configure ssh server as backup access"
	OPT10="Setup shortcut commands for convenience"
	OPT11="Configure Hypernets startup services"
 	OPT12="Quit"
	options=(
		"$OPT1"
		"$OPT2"
		"$OPT3"
		"$OPT4"
		"$OPT5"
		"$OPT6"
		"$OPT7"
		"$OPT8"
		"$OPT9"
		"$OPT10"
		"$OPT11"
		"$OPT12"
	)

	select opt in "${options[@]}"
	do
		case $opt in 
			"$OPT1") # "Update hypernets_tools"
				check_if_online
				update_repo
				break
				;;
			"$OPT2") # "Install dependencies"
				check_if_online
				install_dependencies
				break
				;;
			"$OPT3") # "Download and install YoctoHub"
				check_if_online
				download_yoctohub
				break
				;;
			"$OPT4") # "Run Yocto-Pictor auto-configuration"
				auto_config_yocto
				break
				;;
			"$OPT5") # "Install / update libhypstar"
				check_if_online
				update_libhypstar
				break
				;;
			"$OPT6") # "Configure ports"
				configure_port
				break
				;;
			"$OPT7") # "Setup rain sensor"
				setup_rain_sensor
				break
				;;
			"$OPT8") # "Operating system configuration"
				os_config
				break
				;;
			"$OPT9") # "Configure ssh server as backup access"
				setup_backdoor
				break
				;;
			"$OPT10") # "Setup shortcut commands for convenience"
                ./install/08_setup_shortcuts.sh
				break
				;;
			"$OPT11") # "Configure Hypernets startup services"
                setup_services
				break
				;;
			"$OPT12") # "Quit"
                exit 0
				break
				;;
			*)
				echo -e "\nInvalid choice!\n"
				break
				;;
		esac
	done
done
}

# TODO: error handler
print_logo
check_sudo_user
main_menu
