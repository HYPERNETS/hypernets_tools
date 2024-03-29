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

# Make Logs
echo "Making Logs..."
mkdir -p LOGS

logNameBase=$(date +"%Y-%m-%d-%H%M")

suffixeName=""
for i in {001..999}; do
	if [ -f "LOGS/$logNameBase$suffixeName-sequence.log" ]; then 
		echo "[DEBUG]  Error the log already exists! ($i)"
		suffixeName=$(echo "-$i")
	else
		logNameBase=$(echo $logNameBase$suffixeName)
		break
	fi
done


disk_usage() {
    logNameBase=$1

    echo "Disk usage informations:" 
    df -h -text4

    diskUsageOuput="LOGS/disk-usage.log"
    dfOutput=$(df -text4 --output=used,avail,pcent)

    if [ ! -f  $diskUsageOuput ] ; then
        echo "[INFO] Creation of $diskUsageOuput"
        echo -n "DateTime    " > $diskUsageOuput
        echo "$dfOutput" | sed 2d >> $diskUsageOuput
    fi
    echo -n "$logNameBase " >> $diskUsageOuput
    echo "$dfOutput" | sed 1d >> $diskUsageOuput
}

make_log() {
	logNameBase=$1
	logName=$2

	set +e
	systemctl is-enabled hypernets-$logName.service > /dev/null
	if [[ $? -eq 0 ]] ; then
		echo "[DEBUG]  Making log: $logName..."
		journalctl -b-1 -u hypernets-$logName --no-pager > LOGS/$logNameBase-$logName.log
	else
		echo "[DEBUG]  Skipping log: $logName."
	fi
	set -e
}

make_log $logNameBase sequence
make_log $logNameBase hello
make_log $logNameBase access
make_log $logNameBase time
make_log $logNameBase webcam
disk_usage $logNameBase

# We check if network is on
echo "Waiting for network..."
nm-online
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

# We first make sure that server is up
set +e
for i in {1..30}
do
	# Update the datetime flag on the server
	echo "(attempt #$i) Touching $ipServer:$remoteDir/system_is_up"
	ssh -p $sshPort -t $ipServer "touch $remoteDir/system_is_up" > /dev/null 2>&1
	if [[ $? -eq 0 ]] ; then
		echo "Server is up!"
		break
	fi
	echo "Unsuccessful, sleeping 10s..."
	sleep 10
done
set -e

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

if [ -d "OTHER" ]; then
	echo "Syncing Directory OTHER..."
    # rt -> r XXX
	rsync --ignore-existing -e "ssh -p $sshPort" -r "OTHER" "$ipServer:$remoteDir"
	# rsync -e "ssh -p $sshPort" -rt "OTHER" "$ipServer:$remoteDir"
fi

echo "End."
