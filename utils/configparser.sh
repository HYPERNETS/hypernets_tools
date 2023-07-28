#!/bin/bash -
#===============================================================================
#
#          FILE: configparser.sh
#
#         USAGE: source configparser.sh
#
#   DESCRIPTION: 
#       OPTIONS: ---
#        AUTHOR: Alexandre CORIZZI, alexandre.corizzi@obs-vlfr.fr
#  ORGANIZATION: Laboratoire d'oceanographie de Villefranche-sur-mer (LOV)
#       CREATED: 23/04/2021 09:26
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode

parse_config () {
	keyword="$1"
	config_file="$2"

	if [[ ! -f "$config_file" ]]; then
		>&2 echo "Config file $config_file not found"
		exit -1
	fi
	
	value=$(awk -F "[=]" '/^'$keyword'/ {print $2; exit}' $config_file)
	value=$(echo "$value" | tr -d ' ')
	echo $value
}
