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

if [[ "${1-}" == "-h" ]] || [[ "${1-}" == "--help" ]]; then
	echo "$0 [-h|--help] [--test-run]"
	echo
	echo "Without options run the fully automated sequence"
	echo
	echo "  --test-run   override config_dynamic.ini by keep_pc = on"
	echo "  -h, --help   print this help"
	echo 
	exit 
fi

# add ~/.local/bin to path, Yocto command line API is installed there in Manjaro
PATH="$PATH:~/.local/bin"

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
debugYocto=$(parse_config "debug_yocto" config_static.ini)

# Test run, don't send yocto to sleep and don't ignore the sequence
if [[ "${1-}" == "--test-run" ]]; then
	keepPc="on"
	keepPcInConf=$(parse_config "keep_pc" config_dynamic.ini)
else	
	keepPc=$(parse_config "keep_pc" config_dynamic.ini)
fi


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

		# Sync PC clock to yocto gps if more than 5 sec out of sync
		# and yocto gps has fix
		set +e
		utils/sync_clock_to_gps.sh -m 5
		set -e

		# log next scheduled yocto wakeup if yocto command line API is installed
		if [[ $(command -v YWakeUpMonitor) ]]; then
			yocto=$(parse_config "yocto_prefix2" config_static.ini)
			yocto_time=$(YRealTimeClock -f '[result]' -r 127.0.0.1 $yocto get_dateTime)
			next_wakeup_timestamp=$(YWakeUpMonitor -f '[result]' -r 127.0.0.1 $yocto get_nextWakeUp|sed -e 's/[[:space:]].*//')
			yocto_offset=$(YRealTimeClock -f '[result]' -r 127.0.0.1 $yocto get_utcOffset)

			if [ "$yocto_offset" = 0 ]; then
				utc_offset=""
			else
				utc_offset=$(printf "%+d" $(("$yocto_offset" / 3600)))
			fi

			if [ "$next_wakeup_timestamp" = 0 ]; then
				echo "[WARNING]  Yocto scheduled wakeup is disabled !!"
			else
				yocto_timestamp=$(date -d "$yocto_time UTC" -u +%s)
				delta=$(( "$next_wakeup_timestamp" - "$yocto_timestamp" ))
				echo "[INFO]  Next Yocto wakeup is scheduled on $(date -d @$next_wakeup_timestamp '+%Y/%m/%d %H:%M:%S') UTC$utc_offset (in $delta s)"
			fi
		fi # log next scheduled yocto wakeup if yocto command line API is installed
    fi # [[ "$bypassYocto" != "yes" ]] && [[ "$startSequence" == "yes" ]]

	## Log network traffic
	## interface1 Rx Tx,interface2 Rx Tx,....
	traffic=$(grep : /proc/net/dev | sed -e 's/^[[:space:]]\+//;s/[[:space:]]\+/ /g;s/://g'| cut -d " " -f 1,2,10 | paste -sd ",")
	echo "[INFO]  Network traffic:$traffic"

	# check minimum uptime
    if [[ "$keepPc" == "off" ]]; then
		uptime=$(sed -e 's/\..*//' /proc/uptime)

		## minimum allowed uptime is 2 minutes for successful sequence (exit code 0)
		## and rain (exit code 88), and 5 minutes for all other failed sequences
		if [[ "$return_value" == "0" ]] || [[ "$return_value" == "88" ]] ; then
			min_uptime=120
		else
			min_uptime=300
		fi

		## take a nap if necessary
		if (( $uptime < $min_uptime )); then
			let sleep_duration=$min_uptime-$uptime
			echo "[INFO]  Sequence duration was $uptime seconds (min. allowed $min_uptime s)"
			echo "[INFO]  Sleeping for $sleep_duration s..."

			sleep $sleep_duration
		fi
	fi # "$keepPc" == "off"

	# Sleep inhibited by sleep.lock
	if [ -f sleep.lock ]; then
		keepPc="on"
		sleepLocked=1
	fi

    if [[ "$keepPc" == "off" ]]; then
	    echo "[INFO]  Option : Keep PC OFF"

	    echo "[INFO]  Send Yoctopuce To sleep (or not)"
		set +e
	    python -m hypernets.yocto.sleep_monitor
		yocto_sleep=$?
		set -e

		echo "[DEBUG] Yoctosleep status : $yocto_sleep"

		if [[ $yocto_sleep -eq 0 ]]; then
			# All OK, shuttig down
			echo "[DEBUG] Shutting down"
			exit 0
		fi

		# Something went wrong
	    # Cause service exit 1 and doesn't execute SuccessAction=poweroff
		if [[ $yocto_sleep -eq 1 ]]; then
			echo "[CRITICAL] Yocto unreachable !!"
		elif [[ $yocto_sleep -eq 255 ]]; then
			echo "[CRITICAL] Yocto scheduled wakeup is disabled !!"
			echo "[CRITICAL] Waking up is possible ONLY by manually pressing 'WAKE' button !!"
		fi

		echo "[CRITICAL] NOT shutting down !!"
	    exit 1
    else
	    echo "[INFO]  Option : Keep PC ON"

		# Test run
		if [[ "${keepPcInConf-}" == "off" ]]; then
			echo "-----------------------------------"
			echo "keep_pc = off in config_dynamic.ini"
			echo "Automated sequence would have shut down the PC"
			echo
		fi

		# sleep inhibited by sleep.lock file
		if [[ "${sleepLocked-}" == 1 ]]; then
			echo "[ERROR] Power off has been inhibited by sleep.lock file in the hypernets_tools folder"
			echo "[ERROR] Remove the sleep.lock file to enable sending yocto to sleep and powering off the PC"
			echo
		fi

	    # Cause service exit 1 and doesnt execute SuccessAction=poweroff
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


## log hypernets_tools repo and branch
set +e
hn_tools_repo=$(git config --get remote.origin.url)
if [[ $? -ne 0 ]] ; then
	set -e
	echo "[WARNING]  hypernets_tools is not inside a git working tree"
else
	git update-index -q --refresh > /dev/null 2>&1
	hn_tools_branch=$(git branch --show-current)
	hn_tools_commit=$(git rev-parse --short HEAD)
	if [[ $(git status --porcelain) != "" ]]; then
		hn_tools_commit="${hn_tools_commit}-mod"
	fi

	echo "[INFO]  Running hypernets_tools from $hn_tools_repo branch $hn_tools_branch commit $hn_tools_commit"
fi
set -e


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

		# Check if yocto is accessible
		yocto=$(parse_config "yocto_prefix2" config_static.ini)
		set +e
		wget -O- "http://127.0.0.1:4444/bySerial/$yocto/api.txt" > /dev/null 2>&1
		retcode=$?
		if [[ $retcode == 0 ]]; then
			echo "[INFO]  Found Yocto"
		elif [[ $retcode == 8 ]]; then 
			# Server issued an error response. Probably 404 not found.
			echo "[CRITICAL] Yocto '$yocto' is not accessible !!"

			# list modules if command line API is installed
			if [[ $(command -v YModule) ]]; then
				inventory=$(YModule -r 127.0.0.1 inventory)
				echo "[CRITICAL] The list of modules found:"
				echo "$inventory"
			fi

			echo "[CRITICAL] Can't do anything without Yocto !!"
			echo "[CRITICAL] Exiting the sequence !!"
			exit -1
		else
			# Some other wget error
			echo "[ERROR] Yocto request finished with error code $retcode"
		fi
		set -e
	fi

	# log supply voltage
	voltage=$(python -m hypernets.yocto.voltage)
	echo "[INFO]  Supply voltage: $voltage V"

	# log wake up reason
	set +e
	wakeupreason=$(python -m hypernets.yocto.wakeupreason)
	set -e
	echo "[INFO]  Wake up reason is : $wakeupreason."

	if [[ "$checkWakeUpReason" == "yes" ]] ; then
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

	# Sync PC clock to yocto gps if more than 5 sec out of sync
	# and yocto gps has fix
	set +e
	utils/sync_clock_to_gps.sh -m 5
	set -e
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

		# There is no point in trying again in case of some errors:
		# 30 - sequence file not found
		# 88 - rainig
		if [ $return_value -ne 30 ] && [ $return_value -ne 88 ]; then
			sleep 1

			## VM stabilisation failed
			## power cycle, otherwise the second attempt fails as well
			if [ $return_value -eq 78 ]; then
				echo "[INFO]  Power cycling the radiometer"
				python -m hypernets.yocto.relay -soff -n3
				sleep 10
				python -m hypernets.yocto.relay -son -n3
			fi

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
