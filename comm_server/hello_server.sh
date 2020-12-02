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

sleep 30

ipServer=$(awk -F "= " '/credentials/ {print $2}' config_hypernets.ini)

# Update the datetime flag on the server
ssh -t $ipServer 'touch ~/system_is_up' > /dev/null 2>&1 

# Sync Config Files
source comm_server/bidirectional_sync.sh

bidirectional_sync "config_hypernets.ini" \
	"$ipServer" "~/config_hypernets.ini"

# Send data
rsync -rt --exclude "CUR*" "DATA" "$ipServer:/home/hypernets/public_html/r2d2-beta"

# Sync the whole config folder from remote to local
# rsync -rt "$ipServer:~/config/" "/opt/pyxis/config/"

# Set up the reverse ssh
# bash /opt/corsica/scripts/comm_server/reverse_ssh.sh
