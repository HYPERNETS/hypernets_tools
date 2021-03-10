#!/usr/bin/bash

# If issues : 
# use autossh with an independant service : 
# see : https://gist.github.com/thomasfr/9707568


# -f : stdin > /dev/null
#
# -N : do not execute remote command (usefull for just forwarding port)
#
# -R : Specifies that connections to the given TCP port or Unix socket on 
#      the remote (server) host are to be forwarded to the local side. 

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode	


reverse_ssh(){
	ipServer="$1"
	sshPort="$2"
	pathToPortFile="$3"

	ssh -p $sshPort -o "ExitOnForwardFailure yes" -f -N -R0:127.0.0.1:22 $ipServer > /tmp/ssh_last 2>&1
	ssh -p $sshPort $ipServer "cat >> $pathToPortFile" < /tmp/ssh_last 
}
