#!/usr/bin/bash

XHL=$(tput setaf 9) ## red
RESET_HL=$(tput sgr0) ## reset all text formatting

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./install/${0##*/} instead"
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

user=$(logname)

home=$(eval echo "~$user")

if [ "$ID"  == "manjaro" ]; then
	sed -i '/\.bash_aliases/d' $home/.bashrc

	echo "if [ -f ~/.bash_aliases ]; then . ~/.bash_aliases; fi" >> $home/.bashrc
fi

echo
echo "Setting up command line tools in $home/.bash_aliases"
echo
echo "Run the following line for importing into active shell instance"
echo ". $home/.bash_aliases"
echo

rm -f $home/.bash_aliases
sudo -u $user touch $home/.bash_aliases

cat << EOF >> $home/.bash_aliases
# This file is generated and installed by hypernets_tools
#
# It contains the definitions and aliases of command line tools
# and executes commands() in the end which prints the help text

HYPERNETS_TOOLS=$PWD
EOF

cat install/bash_aliases >> $home/.bash_aliases

