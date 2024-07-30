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
	remoteDate=$(ssh -p "$sshPort" -t "$remoteAccess" \
		"stat -c %y $remotePath 2> /dev/null"\
		2> /dev/null)

	if [[ "$?" -eq 1 ]]; then
		echo "[INFO]  $0 : Remote file does not exist"
		scp -P "$sshPort" "$localPath" "$remoteAccess:$remotePath"
		return $?
	fi

	localDate=$(stat -c %y "$localPath" 2> /dev/null)
	if [[ "$?" -eq 1 ]]; then
		echo "[INFO]  $0 : Local file does not exist"
		scp -P "$sshPort" "$remoteAccess:$remotePath" "$localPath"
		return $?
	fi
	set -e  # Back to strict mode

	# Conversion in integer
	remoteDate=$(date -d "$remoteDate" +%s)
	localDate=$(date -d "$localDate" +%s)

	# Both files exists, compare of datetimes and sync
	if [ "$remoteDate" -gt "$localDate" ] ; then
		echo "[INFO]  Sync from remote to local"
		rsync -e "ssh -p $sshPort" -vt "$remoteAccess:$remotePath" "$localPath"
	elif [ "$remoteDate" -lt "$localDate" ] ; then
		echo "[INFO]  Sync from local to remote"
		rsync -e "ssh -p $sshPort" -vt "$localPath" "$remoteAccess:$remotePath"
	else
		echo "[INFO]  Files are synchronized."
	fi
	return $?
}
