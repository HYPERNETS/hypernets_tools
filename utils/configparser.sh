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

## define text highlights
XHL=$(tput setaf 9) ## red
RESET_HL=$(tput sgr0) ## reset all text formatting

parse_config () {
	keyword="$1"
	config_file="$2"

	if [[ ! -f "$config_file" ]]; then
		>&2 echo "${XHL}Config file $config_file not found${RESET_HL}"
		exit -1
	fi
	
	value=$(awk -F "[=]" '/^'$keyword'/ {print $2; exit}' $config_file)
	value=$(echo "$value" | tr -d ' ')
	echo $value
}
