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


echo "Sleep 30 sec"
sleep 30

# Read config file :
ipServer=$(awk -F "= " '/credentials/ {print $2}' config_hypernets.ini)
remoteDir=$(awk -F "= " '/remote_dir/ {print $2}' config_hypernets.ini)
sshPort=$(awk -F "= " '/ssh_port/ {print $2; exit}' config_hypernets.ini)

if [ -z $sshPort ]; then
	sshPort="22"
fi

# Trim strings : 
shopt -s extglob
ipServer=${ipServer%%*( )}
remoteDir=${remoteDir%%*( )}
sshPort=${sshPort%%*( )}
shopt -u extglob

# Make Logs
mkdir -p LOGS
journalctl -eu hypernets-sequence -n 1500 --no-pager > LOGS/hypernets-sequence.log
journalctl -eu hypernets-hello -n 150 --no-pager > LOGS/hypernets-hello.log

# Update the datetime flag on the server
echo "Touching $ipServer:$remoteDir/system_is_up"
ssh -p $sshPort -t $ipServer "touch $remoteDir/system_is_up" > /dev/null 2>&1 

# Sync Config Files
source comm_server/bidirectional_sync.sh

bidirectional_sync "config_hypernets.ini" \
	"$ipServer" "$remoteDir/config_hypernets.ini.$USER" "$sshPort"

git pull

# Send data
echo "Syncing Data..."
rsync -e "ssh -p $sshPort" -rt --exclude "CUR*" "DATA" "$ipServer:$remoteDir"
echo "Syncing Logs..."
rsync -e "ssh -p $sshPort" -rt "LOGS" "$ipServer:$remoteDir"

# Set up the reverse ssh
source comm_server/reverse_ssh.sh
reverse_ssh $ipServer $sshPort "$remoteDir/ssh_ports"
