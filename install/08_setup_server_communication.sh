#!/usr/bin/bash

set -o nounset
set -euo pipefail


if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : sudo ./install/${0##*/} instead"
	exit 1
fi


credentials=$(awk -F "= " '/credentials/ {print $2; exit}' config_hypernets.ini)
remoteDir=$(awk -F "= " '/remote_dir/ {print $2; exit}' config_hypernets.ini)

echo "Read from config_hypernets.ini : "
echo " * Server credentials : $credentials"
echo " * Remote directory : $remoteDir"
read -p "   Confirm (y/n) ?" -rn1
echo


if [[ $REPLY =~ ^[Yy]$ ]]; then 
	echo
	user="$SUDO_USER"
	read -p "Copy ssh-id ? \n (NPL server : yes / RBINS server : no)" -rn1
	echo

	if [[ $REPLY =~ ^[Yy]$ ]]; then 
		sudo -u $user ssh-keygen -t rsa
		sudo -u $user ssh-copy-id -i /home/$user/.ssh/id_rsa $credentials
	fi

	path_to_service=$(echo "$PWD/comm_server/hello_server.sh" | sed 's/\//\\\//g')
	path_to_h_tools=$(echo "$PWD" | sed 's/\//\\\//g')

	service_file="/etc/systemd/system/hypernets-hello.service"

	cp "./install/hypernets-hello.service"  $service_file

	sed -i '/User=$/s/$/'$user'/' $service_file
	sed -i '/ExecStart=$/s/$/'$path_to_service'/' $service_file
	sed -i '/WorkingDirectory=$/s/$/'$path_to_h_tools'\//' $service_file

	systemctl enable hypernets-hello
	systemctl start hypernets-hello
	journalctl --follow -u hypernets-hello
else
	echo "Exit"
	exit 1
fi
