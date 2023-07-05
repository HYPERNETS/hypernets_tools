#!/usr/bin/bash

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./install/${0##*/} instead"
	exit 1
fi

if [[ $EUID -eq 0 ]]; then
	user=$SUDO_USER
else
	user=$(whoami)
fi

home=$(eval echo "~$user")

echo
echo "Setting up shortcuts in $home/.bash_aliases"

cat << EOF > $home/.bash_aliases
# This file is generated and installed by hypernets_tools
#
# It contains the definitions and aliases of command shortcuts
# and executes commands() in the end which prints the help text

HYPERNETS_TOOLS=$PWD
EOF

cat install/bash_aliases >> $home/.bash_aliases

