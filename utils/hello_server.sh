#!/bin/bash - 
#===============================================================================
#
#          FILE: hello_server.sh
# 
#         USAGE: ./hello_server.sh 
# 
#   DESCRIPTION: Establish connection with server
#                Synchronize /config directory both ways
#                Set-up reverse ssh to make server able to access to host system
# 
#       OPTIONS: ---
#         NOTES: ---
#        AUTHOR: Alexandre CORIZZI, alexandre.corizzi@obs-vlfr.fr
#  ORGANIZATION: 
#       CREATED: 05/03/2020 15:53
#      REVISION: 23/10/2020 17:19
#s===============================================================================

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode	


# echo "Sleep 30 sec"
# sleep 30

# We ping Google DNS to check if network is up
echo "Waiting for network..."
while ! timeout 2 ping -c 1 -n 8.8.8.8 &>/dev/null
do
	echo -n '.'
done
echo "Ok !"


# Read config file :
source utils/configparser.sh

ipServer=$(parse_config "credentials" config_static.ini)
remoteDir=$(parse_config "remote_dir" config_static.ini)
sshPort=$(parse_config "ssh_port" config_static.ini)
autoUpdate=$(parse_config "auto_update" config_dynamic.ini)

if [ -z $sshPort ]; then
	sshPort="22"
fi

if [ -z $autoUpdate ]; then
	autoUpdate="no"
fi

# Make Logs
mkdir -p LOGS


logNameBase=$(date +"%Y-%m-%d-%H%M")

journalctl -b-1 -u hypernets-sequence --no-pager > LOGS/$logNameBase-sequence.log
journalctl -b-1 -u hypernets-hello --no-pager > LOGS/$logNameBase-hello.log
journalctl -b-1 -u hypernets-access --no-pager > LOGS/$logNameBase-access.log

# journalctl -eu hypernets-sequence -n 15000 --no-pager > LOGS/hypernets-sequence.log
# journalctl -eu hypernets-hello -n 150 --no-pager > LOGS/hypernets-hello.log
# journalctl -eu hypernets-access -n 150 --no-pager > LOGS/hypernets-access.log


# Update the datetime flag on the server
echo "Touching $ipServer:$remoteDir/system_is_up"
ssh -p $sshPort -t $ipServer "touch $remoteDir/system_is_up" > /dev/null 2>&1 

# Sync Config Files
source utils/bidirectional_sync.sh

bidirectional_sync "config_dynamic.ini" \
	"$ipServer" "$remoteDir/config_dynamic.ini.$USER" "$sshPort"

if [[ ! "$autoUpdate" == "no" ]] ; then
	echo "Auto Update ON"
	set +e
	git pull
	if [ $? -ne 0 ]; then echo "Can't pull : do you have local change ?" ; fi
	set -e
fi

# Send data
echo "Syncing Data..."
rsync -e "ssh -p $sshPort" -rt --exclude "CUR*" "DATA" "$ipServer:$remoteDir"
echo "Syncing Logs..."
rsync -e "ssh -p $sshPort" -rt "LOGS" "$ipServer:$remoteDir"

# Set up the reverse ssh
# source utils/reverse_ssh.sh
# reverse_ssh $ipServer $sshPort "$remoteDir/ssh_ports"
