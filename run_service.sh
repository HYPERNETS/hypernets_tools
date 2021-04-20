#!/bin/bash -
#===============================================================================
#
#          FILE: run_service.sh
#
#         USAGE: ./run_service.sh
#
#   DESCRIPTION: Script called by systemd to run a sequence at boot time # #       
#       OPTIONS: ---
#        AUTHOR: Alexandre CORIZZI, alexandre.corizzi@obs-vlfr.fr
#  ORGANIZATION: Laboratoire d'oceanographie de Villefranche-sur-mer (LOV)
#       CREATED: 22/10/2020 18:19
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode


# Only first entry is returned with exit [FIXME : better ?]
startSequence=$(awk -F "[ =]+" '/start_sequence/ {print $2 ; exit}' config_hypernets.ini)
bypassYocto=$(awk -F "[ =]+" '/bypass_yocto/ {print $2 ; exit}' config_hypernets.ini)
hypstarPort=$(awk -F "[ =]+" '/hypstar_port/ {print $2 ; exit}' config_hypernets.ini)
baudrate=$(awk -F "[ =]+" '/baudrate/ {print $2 ; exit}' config_hypernets.ini)
loglevel=$(awk -F "[ =]+" '/loglevel/ {print $2 ; exit}' config_hypernets.ini)

extra_args=""
if [[ "$startSequence" == "no" ]] ; then
	echo "Start sequence = no"
	exit 1
fi

if [[ -n $hypstarPort ]] ; then
	extra_args="$extra_args -p $hypstarPort"
fi

if [[ -n $baudrate ]] ; then
	extra_args="$extra_args -b $baudrate"
fi

if [[ -n $loglevel ]] ; then
	extra_args="$extra_args -l $loglevel"
fi

# Ensure Yocto is online
if [[ "$bypassYocto" == "no" ]] ; then
	yoctopuceIP=$(awk -F "[ =]+" '/yoctopuce_ip/ {print $2; exit}' config_hypernets.ini)
	echo "Waiting for yoctopuce..."
	while ! timeout 2 ping -c 1 -n $yoctopuceIP &>/dev/null
	do
		echo .	
	done
	echo "Ok !"

	python -m hypernets.scripts.relay_command -n2 -son
	python -m hypernets.scripts.relay_command -n3 -son
	sleep 1
	python -m hypernets.scripts.relay_command -n5 -son
	python -m hypernets.scripts.relay_command -n6 -son
	echo "Sleeping 30s... (old firmware issue)"
	sleep 30

else
	echo "Bypassing Yocto"
    extra_args="$extra_args --noyocto"
fi

sequence_file=$(awk -F "[ =]+" '/sequence_file/ {print $2; exit}' config_hypernets.ini)

# sequence_file="hypernets/resources/sequences_samples/sequence_picture_sun.csv"
echo $sequence_file

shutdown_sequence() {
    if [[ "$bypassYocto" == "no" ]] ; then
	    python -m hypernets.scripts.relay_command -n2 -soff
	    python -m hypernets.scripts.relay_command -n3 -soff
	    sleep 1
	    python -m hypernets.scripts.relay_command -n5 -soff
	    python -m hypernets.scripts.relay_command -n6 -soff
    fi

    keepPc=$(awk -F "[ =]+" '/keep_pc/ {print $2; exit}' config_hypernets.ini)

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
}

exit_actions() {
    return_value=$?
    if [ $return_value -eq 0 ] ; then
        echo "Success"
        shutdown_sequence;
    else
    	echo "Hysptar scheduled job exited with code $return_value";
    fi
}

trap "exit_actions" EXIT
python3 -m hypernets.open_sequence -df $sequence_file $extra_args
