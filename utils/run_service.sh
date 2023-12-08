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


if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
	echo "This script must be run from hypernets_tools folder" 1>&2
	echo "Use : ./utils/${0##*/} instead"
	exit 1
fi


source utils/configparser.sh

# Hypstar Configuration:
baudrate=$(parse_config "baudrate" config_dynamic.ini)
hypstarPort=$(parse_config "'hypstar_port" config_dynamic.ini)
bypassYocto=$(parse_config "bypass_yocto" config_static.ini)
loglevel=$(parse_config "loglevel" config_dynamic.ini)
bootTimeout=$(parse_config "boot_timeout" config_dynamic.ini)
swirTec=$(parse_config "swir_tec" config_dynamic.ini)
verbosity=$(parse_config "verbosity" config_dynamic.ini)
dumpEnvironmentLogs=$(parse_config "log_environment" config_dynamic.ini)

# Starting Conditions:
sequence_file=$(parse_config "sequence_file" config_dynamic.ini)
sequence_file_alt=$(parse_config "sequence_file_alt" config_dynamic.ini)

checkWakeUpReason=$(parse_config "check_wakeup_reason" config_dynamic.ini)
checkRain=$(parse_config "check_rain" config_dynamic.ini)
startSequence=$(parse_config "start_sequence" config_dynamic.ini)
keepPc=$(parse_config "keep_pc" config_dynamic.ini)
debugYocto=$(parse_config "debug_yocto" config_static.ini)

shutdown_sequence() {
	return_value="$1"

    if [[ "$bypassYocto" != "yes" ]] && [[ "$startSequence" == "yes" ]] ; then
		# log supply voltage before switching off the relays
		voltage=$(python -m hypernets.yocto.voltage)
		echo "[INFO]  Supply voltage: $voltage V"

	    echo "[INFO]  Set relays #2 and #3 to OFF."
	    python -m hypernets.yocto.relay -soff -n2 -n3

		if [[ "$checkRain" == "yes" ]]; then
	    	echo "[INFO]  Set relay #4 to OFF."
		    python -m hypernets.yocto.relay -soff -n4
		fi
    fi

    if [[ "$keepPc" == "off" ]]; then
	    echo "[INFO]  Option : Keep PC OFF"

	    echo "[INFO]  Send Yoctopuce To sleep (or not)"
		set +e
	    python -m hypernets.yocto.sleep_monitor
		yocto_sleep=$?
		set -e

		echo "[DEBUG] Yoctosleep status : $yocto_sleep"
		if [[ ! $yocto_sleep -eq 0 ]]; then
			 echo "[CRITICAL] Yocto unreachable !!"
		fi
	    exit 0
    else
	    # Cause service exit 1 and doesnt execute SuccessAction=poweroff
	    echo "[INFO]  Option : Keep PC ON"
	    exit 1
    fi
}



debug_yocto(){
    # ------------------------------------------------------------------------------
    # YOCTO DEBUG ------------------------------------------------------------------
    # ------------------------------------------------------------------------------
    echo "[DEBUG]  Check if Yocto-Pictor is in (pseudo) deep-sleep mode..."
    yoctoPrefix2=$(parse_config "yocto_prefix2" config_static.ini)
    set +e
    yoctoState=$(wget -O- \
        'http://127.0.0.1:4444/bySerial/$yoctoPrefix2/api/wakeUpMonitor/wakeUpState' \
        2> /dev/null)

    if [[ ! $? -eq 0 ]] ; then
        echo "[DEBUG]  Fail to get Yocto-Pictor wake-up state !"
        return 1
    fi

    echo "[DEBUG]  Yocto-Pictor wake-up state : $yoctoState"

    if [[ $yoctoState == "SLEEPING" ]] ; then
        echo "[DEBUG]  Awaking Yocto-Pictor..."
        yoctoState=$(wget -O- \
            'http://127.0.0.1:4444/bySerial/$yoctoPrefix2/api/wakeUpMonitor?wakeUpState=1' \
            2> /dev/null)
                    if [[ ! $? -eq 0 ]] ; then
                        echo "[DEBUG]  Fail to wake-up the Yocto-Pictor !"
                        return 1
                    fi
                    sleep 2
    fi

    logNameBase=$(date +"%Y-%m-%d-%H%M")

    suffixeName=""
    for i in {001..999}; do
        if [ -f "OTHER/$logNameBase$suffixeName-log.txt" ] ||
            [ -f "OTHER/$logNameBase$suffixeName-api.txt" ]; then
                    echo "[DEBUG]  Error the log already exists! ($i)"
                    suffixeName=$(echo "-$i")
                else
                    logNameBase=$(echo $logNameBase$suffixeName)
                    break
        fi
    done

    echo "[DEBUG]  Getting LOGS.txt and API.txt (prefix: $logNameBase)..."

    wget -O- 'http://127.0.0.1:4444/bySerial/$yoctoPrefix2/api.txt' > \
        "OTHER/$logNameBase-api.txt" 2> /dev/null

    wget -O- 'http://127.0.0.1:4444/bySerial/$yoctoPrefix2/logs.txt' > \
        "OTHER/$logNameBase-log.txt" 2> /dev/null

    set -e
    # ------------------------------------------------------------------------------
    # \ YOCTO DEBUG ----------------------------------------------------------------
    # ------------------------------------------------------------------------------
}

# log operating system release
if [ -f /etc/os-release ]; then
	source /etc/os-release
fi

# for manjaro read version from /etc/lsb-release
if [[ "$ID" == "manjaro" ]]; then
	if [ -f /etc/lsb-release ]; then
		source /etc/lsb-release
		PRETTY_NAME="${PRETTY_NAME-} ${DISTRIB_RELEASE-}"
	fi
elif [ -f /etc/debian_version ]; then
	PRETTY_NAME="${PRETTY_NAME-} version $(cat /etc/debian_version)"
fi

echo "[INFO]  Running on ${PRETTY_NAME-}"


if [[ "$bypassYocto" != "yes" ]] ; then

    if [[ "$debugYocto" == "yes" ]] ; then
        debug_yocto
    fi

	# Ensure Yocto is online
	yoctopuceIP=$(parse_config "yoctopuce_ip" config_static.ini)

	if [[ "$yoctopuceIP" != "usb" ]] ; then
		# We ping it if there is an IP address
		echo "[INFO]  Waiting for yoctopuce..."
		while ! timeout 2 ping -c 1 -n $yoctopuceIP &>/dev/null
		do
			echo -n '.'
		done
		echo "[INFO]  Ok !"
	else
		# Else check  if VirtualHub is running
		set +e
		systemctl is-active yvirtualhub.service > /dev/null
		if [[ $? -eq 0 ]] ; then
			set -e
			echo "[INFO]  VirtualHub is running."
		else
			set -e
			echo "[INFO]  Starting VirtualHub..."
            if [[ "$ID" == "manjaro" ]]; then
			    /usr/bin/VirtualHub &
            elif [[ "$ID" == "debian" ]]; then
                /usr/sbin/VirtualHub &
            else
                echo "[ERROR] Not able to identify the distribution."
                exit 0
            fi
			sleep 2
			echo "[INFO]  ok"
		fi
	fi

	# log supply voltage
	voltage=$(python -m hypernets.yocto.voltage)
	echo "[INFO]  Supply voltage: $voltage V"

	if [[ "$checkWakeUpReason" == "yes" ]] ; then
		echo "[INFO]  Check Wake up reason..."
		set +e
		wakeupreason=$(python -m hypernets.yocto.wakeupreason)
		set -e

		echo "[DEBUG]  Wake up reason is : $wakeupreason."
        


		if [[ "$wakeupreason" != "SCHEDULE"* ]]; then
			echo "[WARNING]  $wakeupreason is not a reason to start the sequence."
			startSequence="no"
			if [[ "$keepPc" != "on" ]]; then
				echo "[DEBUG]  Security sleep 2 minutes..."
				sleep 120
			fi
			shutdown_sequence 0
		fi

		if [[ "$wakeupreason" == "SCHEDULE2" ]]; then
            if [[ ! -n $sequence_file_alt ]] ; then
                echo "[WARNING ] No alternative sequence file is defined."
                echo "[WARNING ] $sequence_file will be run instead."
            else
                echo "[INFO    ] $sequence_file_alt as alternative sequence file is defined."
                sequence_file=$sequence_file_alt
            fi 
        fi
	fi # checkWakeUpReason

	if [[ "$checkRain" == "yes" ]] ; then
		echo "[INFO]  Rain sensor check is enabled."
		echo "[INFO]  Set relay #4 to ON."
		python -m hypernets.yocto.relay -son -n4
		sleep 5
	fi # checkRain
fi # bypassYocto != yes

if [[ "$startSequence" == "no" ]] ; then
	echo "[INFO]  Start sequence = no"
	if [[ "$keepPc" != "on" ]]; then
		echo "[INFO]  5 minutes sleep..."
		sleep 300
	fi
	shutdown_sequence 0
fi


extra_args=""

if [[ -n $hypstarPort ]] ; then
	extra_args="$extra_args -p $hypstarPort"
fi

if [[ -n $baudrate ]] ; then
	extra_args="$extra_args -b $baudrate"
fi

if [[ -n $loglevel ]] ; then
	extra_args="$extra_args -l $loglevel"
fi

if [[ -n $bootTimeout ]] ; then
	extra_args="$extra_args -t $bootTimeout"
fi

if [[ "$dumpEnvironmentLogs" == "yes" ]] ; then
	extra_args="$extra_args -e "
fi

if [[ "$checkRain" == "yes" ]] ; then
	extra_args="$extra_args -r "
fi

if [[ -n $swirTec ]] ; then
	extra_args="$extra_args -T $swirTec"
fi

if [[ -n $verbosity ]] ; then
	extra_args="$extra_args -v $verbosity"
fi

if [[ "$bypassYocto" != "yes" ]] ; then
	echo "[INFO]  Set relays #2 and #3 to ON."
	python -m hypernets.yocto.relay -son -n2 -n3

else
	echo "[INFO]  Bypassing Yocto"
    extra_args="$extra_args --noyocto"
fi



exit_actions() {
    return_value=$?
    if [ $return_value -eq 0 ] ; then
        echo "[INFO]  Success"
    else
		echo "[WARNING]  Hysptar scheduled job exited with code $return_value";

		# It is raining
		if [ $return_value -eq 88 ]; then
			echo "[WARNING] Stopping due to rain"
			shutdown_sequence
		fi

		# FIXME : sudo issue
		# if [ $return_value -eq 27 ]; then
		# 	echo "[INFO] Trying to reload and trigger USB rules..."
		# 	sudo udevadm control --reload
		# 	echo $?
		# 	sudo udevadm trigger
		# 	echo $?
		# fi

			echo "[WARNING]  Second try : "
			set +e
			python3 -m hypernets.open_sequence -f $sequence_file $extra_args
			set -e
		fi
    fi
	shutdown_sequence $return_value
}

trap "exit_actions" EXIT
python3 -m hypernets.open_sequence -f $sequence_file $extra_args
