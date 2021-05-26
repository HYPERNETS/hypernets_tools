#!/usr/bin/bash


if [[ ${PWD##*/} != "hypernets_tools" ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./utils/${0##*/} instead"
	exit 1
fi


if [[ $EUID -eq 0 ]]; then
	echo "This script should not be run as root, use $0 (whithout sudo) instead" 1>&2
	exit 1
fi

voila --show_tracebacks=True
# voila --Voila.root_dir=utils/
# voila --Voila.notebook_path=utils/ --debug  #
