#!/usr/bin/bash -

# TODO : add args for specify other credentials

set -o nounset
set -euo pipefail

if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./comm_server/${0##*/} instead"
	exit 1
fi

ipServer=$(awk -F "= " '/credentials/ {print $2}' config_hypernets.ini)
echo $ipServer

set +e
session_name="forward_services"
existing=`tmux ls | grep -o $session_name` 2>&1 > /dev/null
set -e

if [ "$existing" == "$session_name" ]
then
	tmux -2 attach-session -t $session_name
else
	tmux new-session -d -s $session_name > /dev/null
	tmux split-window -h

	tmux select-pane -t 0
	tmux send-keys "jupyter notebook --no-browser" Enter

	tmux select-pane -t 1

    tmux send-keys "./comm_server/forward_services.sh" Enter
fi

