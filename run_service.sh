#!/usr/bin/bash -
#===============================================================================
#
#          FILE: run_service.sh
#
#         USAGE: ./run_service.sh
#
#   DESCRIPTION: Script called by systemd to run a sequence at boot time
#
#       OPTIONS: ---
#        AUTHOR: Alexandre CORIZZI, alexandre.corizzi@obs-vlfr.fr
#  ORGANIZATION: Laboratoire d'oceanographie de Villefranche-sur-mer (LOV)
#       CREATED: 22/10/2020 18:19
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode

echo $PWD

# Ensure Yocto is online
yoctopuceIP=$(awk -F "[ =]+" '/yoctopuce_ip/ {print $2}' config_hypernets.ini)
echo "Waiting for yoctopuce..."
while ! timeout 2 ping -c 1 -n $yoctopuceIP &>/dev/null
do
	echo .	
done
echo "Ok !"

python -m hypernets.scripts.relay_command -n2 -son
python -m hypernets.scripts.relay_command -n3 -son

echo "Waiting for instrument to boot"
sleep 20  # Time for waking up

# sequence_file="hypernets/resources/sequences_samples/sequence_land_STD.csv"
# sequence_file="hypernets/resources/sequences_samples/sequence_water_1_STD.csv"
sequence_file="hypernets/resources/sequences_samples/sequence_1_spectra.csv"

python -m hypernets.open_sequence -df $sequence_file

python -m hypernets.scripts.relay_command -n2 -soff
python -m hypernets.scripts.relay_command -n3 -soff

keepPc=$(awk -F "[ =]+" '/keep_pc/ {print $2}' config_hypernets.ini)

if [[ "$keepPc" == "off" ]]; then
	echo "Option : Keep PC OFF"
	# Send Yoctopuce To sleep (or not)
	python -m hypernets.scripts.sleep_monitor
	exit 0
else
	# Cause service exit 1 and doesnt execute SuccessAction=poweroff
	echo "Option : Keep PC ON"
	exit 1
fi
