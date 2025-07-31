#!/bin/bash - 
#===============================================================================
#
#          FILE: bidirectional_sync.sh
# 
#         USAGE: ./bidirectional_sync.sh  localFile user@remote remoteFile
# 
#   DESCRIPTION: two-way sync between remote and local files
# 
#         NOTES: ---
#        AUTHOR: Alexandre CORIZZI, alexandre.corizzi@obs-vlfr.fr
#  ORGANIZATION: LOV
#       CREATED: 05/03/2020 14:32
#      REVISION:  ---
#s===============================================================================

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode	

bidirectional_sync(){

	localPath="$1"
	remoteAccess="$2"
	remotePath="$3"
	sshPort="$4"

	echo "[INFO]  Sync files : $remoteAccess:$remotePath"
	echo "[INFO]          <->  $localPath"

	set +e  # Temporary allow error in script
	remoteDate=$(ssh -p "$sshPort" -T "$remoteAccess" \
		"stat -c %y $remotePath 2> /dev/null")

	retcode="$?"

	if [[ "$retcode" -eq 1 ]]; then
		echo "[INFO]  $0 : Remote file does not exist, uploading now"
		scp -p -P "$sshPort" "$localPath" "$remoteAccess:$remotePath"
		return $?
	elif [[ "$retcode" -eq 255 || "$remoteDate" == "" ]]; then
		echo "[ERROR]  Failed to retreive remote file modification time"
		return -1
	fi

	localDate=$(stat -c %y "$localPath" 2> /dev/null)
	if [[ "$?" -eq 1 ]]; then
		echo "[INFO]  $0 : Local file does not exist, downloading now"
		scp -p -P "$sshPort" "$remoteAccess:$remotePath" "$localPath"
		return $?
	fi
	set -e  # Back to strict mode

	# Conversion in integer
	remoteTimeStamp=$(date -d "$remoteDate" +%s)
	localTimeStamp=$(date -d "$localDate" +%s)

	# Both files exists, compare of datetimes and sync
	if [ "$remoteTimeStamp" -gt "$localTimeStamp" ] ; then
		echo "[INFO]  Local date: $localDate"
		echo "[INFO]  Remote date: $remoteDate"
		echo "[INFO]  Sync from remote to local"
		rsync -e "ssh -p $sshPort" -vt "$remoteAccess:$remotePath" "$localPath"
	elif [ "$remoteTimeStamp" -lt "$localTimeStamp" ] ; then
		echo "[INFO]  Local date: $localDate"
		echo "[INFO]  Remote date: $remoteDate"
		echo "[INFO]  Sync from local to remote"
		rsync -e "ssh -p $sshPort" -vt "$localPath" "$remoteAccess:$remotePath"
	else
		echo "[INFO]  Files are synchronized."
	fi
	return $?
}
