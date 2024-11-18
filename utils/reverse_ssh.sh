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
	remoteSSHPort="$3"
	verbosity="$4"

    ssh -p $sshPort $verbosity -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" \
	-R$remoteSSHPort:127.0.0.1:22 $ipServer 
}

# Read config file :
source utils/configparser.sh

ipServer="$(parse_config "credentials" config_static.ini)"
sshPort="$(parse_config "ssh_port" config_static.ini)"
remoteSSHPort="$(parse_config "remote_ssh_port" config_static.ini)"
ssh_loglevel="$(parse_config "ssh_loglevel" config_static.ini)"

if [ -z $sshPort ]; then
	sshPort="22"
fi

if [ -z $remoteSSHPort ]; then
	remoteSSHPort="20213"
fi

# Wait until we have connection with the server
set +e
echo "[INFO]  Waiting for network..."
ipServer_ip=$(cut -d "@" -f2 <<< $ipServer)
while true ; do
	if nc -zw1 "$ipServer_ip" "$sshPort" >/dev/null 2>&1
	then
		echo "[INFO]  got response from the network server"
		break
	fi

	sleep 1
done

case $ssh_loglevel in

  DEBUG | DEBUG1)
	verbosity="-v"
    ;;

  DEBUG2)
	verbosity="-vv"
    ;;

  DEBUG3)
	verbosity="-vvv"
    ;;

  ERROR | *)
	verbosity=""
    ;;
esac

# Increase verbosity for every 10th service restart
if [[ "$((($(systemctl show hypernets-access.service -p NRestarts --value)+1)%10))" -eq 0 ]]; then
	verbosity="$verbosity -v"
fi

echo "[-> $sshPort:]$ipServer:$remoteSSHPort"
reverse_ssh "$ipServer" "$sshPort" "$remoteSSHPort" "$verbosity"
