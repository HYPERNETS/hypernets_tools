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
hypstarPort=$(parse_config "hypstar_port" config_dynamic.ini)
bypassYocto=$(parse_config "bypass_yocto" config_static.ini)
loglevel=$(parse_config "loglevel" config_dynamic.ini)
bootTimeout=$(parse_config "boot_timeout" config_dynamic.ini)
swirTec=$(parse_config "swir_tec" config_dynamic.ini)
verbosity=$(parse_config "verbosity" config_dynamic.ini)

# Starting Conditions:
sequence_file=$(parse_config "sequence_file_sched1" config_dynamic.ini)
if [[ "$sequence_file" == "" ]]; then
	sequence_file=$(parse_config "sequence_file" config_dynamic.ini)
fi

sequence_file2=$(parse_config "sequence_file_sched2" config_dynamic.ini)
if [[ "$sequence_file2" == "" ]]; then
	sequence_file2=$(parse_config "sequence_file_alt" config_dynamic.ini)
fi

sequence_file3=$(parse_config "sequence_file_sched3" config_dynamic.ini)

checkWakeUpReason=$(parse_config "check_wakeup_reason" config_dynamic.ini)
checkRain=$(parse_config "check_rain" config_dynamic.ini)
debugYocto=$(parse_config "debug_yocto" config_static.ini)
yoctoPrefix=$(parse_config "yocto_prefix2" config_static.ini)
if [[ "$yoctoPrefix" == "" ]]; then
# host system V4 or newer
    yoctoPrefix=$(parse_config "yocto_prefix3" config_static.ini)
fi


# Test run, don't send yocto to sleep and don't ignore the sequence
if [[ "${1-}" == "--test-run" ]]; then
	keepPc="on"
	keepPcInConf=$(parse_config "keep_pc" config_dynamic.ini)
	startSequence="yes"
	startSequenceInConf=$(parse_config "start_sequence" config_dynamic.ini)
	testRun="yes"
else	
	keepPc=$(parse_config "keep_pc" config_dynamic.ini)
	startSequence=$(parse_config "start_sequence" config_dynamic.ini)
fi

case $verbosity in
  ERROR)
    numeric_verbosity=1
    ;;

  WARNING)
    numeric_verbosity=2
    ;;

  DEBUG)
    numeric_verbosity=4
    ;;

  INFO | *)
    numeric_verbosity=3
    ;;
esac


log_debug() { if [[ $numeric_verbosity -ge 4 ]]; then echo "[DEBUG]  $1"; fi }
log_info() { if [[ $numeric_verbosity -ge 3 ]]; then echo "[INFO]  $1"; fi }
log_warning() { if [[ $numeric_verbosity -ge 2 ]]; then echo "[WARNING]  $1"; fi }
log_error() { if [[ $numeric_verbosity -ge 1 ]]; then echo "[ERROR]  $1"; fi }

shutdown_sequence() {
	return_value="$1"

    if [[ "$bypassYocto" != "yes" ]] && [[ "$startSequence" == "yes" ]] ; then
		# log supply voltage before switching off the relays
		voltage=$(python -m hypernets.yocto.voltage)
		echo "[INFO]  Supply voltage: $voltage V"

	    log_info "Set relays #2 and #3 to OFF."
	    python -m hypernets.yocto.relay -soff -n2 -n3

		if [[ "$checkRain" == "yes" ]]; then
	    	log_info "Set relay #4 to OFF."
		    python -m hypernets.yocto.relay -soff -n4
		fi

		# Sync PC clock to yocto gps if more than 5 sec out of sync
		# and yocto gps has fix
		set +e
		utils/sync_clock_to_gps.sh -m 5 -l $numeric_verbosity
		set -e

		# log next scheduled yocto wakeup if yocto command line API is installed
		if [[ $(command -v YWakeUpMonitor) ]]; then
			yocto_time=$(YRealTimeClock -f '[result]' -r 127.0.0.1 $yoctoPrefix get_dateTime)
			next_wakeup_timestamp=$(YWakeUpMonitor -f '[result]' -r 127.0.0.1 $yoctoPrefix get_nextWakeUp|sed -e 's/[[:space:]].*//')
			yocto_offset=$(YRealTimeClock -f '[result]' -r 127.0.0.1 $yoctoPrefix get_utcOffset)

			if [ "$yocto_offset" = 0 ]; then
				utc_offset=""
			else
				utc_offset=$(printf "%+d" $(("$yocto_offset" / 3600)))
			fi

			if [ "$next_wakeup_timestamp" = 0 ]; then
				log_warning "Yocto scheduled wakeup is disabled !!"
			else
				yocto_timestamp=$(date -d "$yocto_time UTC" -u +%s)
				delta=$(( "$next_wakeup_timestamp" - "$yocto_timestamp" ))
				log_info "Next Yocto wakeup is scheduled on $(date -d @$next_wakeup_timestamp '+%Y/%m/%d %H:%M:%S') UTC$utc_offset (in $delta s)"
			fi
		fi # log next scheduled yocto wakeup if yocto command line API is installed
    fi # [[ "$bypassYocto" != "yes" ]] && [[ "$startSequence" == "yes" ]]

	# check minimum uptime
    if [[ "$keepPc" == "off" ]]; then
		uptime=$(sed -e 's/\..*//' /proc/uptime)

		## minimum allowed uptime is 2 minutes for:
		##   - successful sequence (exit code 0)
		##   - rain (exit code 88)
		##   - imminent yocto watchdog timeout (exit code 98)
		## and 5 minutes for all other failed sequences
		if [[ "$return_value" == "0" ]] || [[ "$return_value" == "88" ]] || [[ "$return_value" == "98" ]]; then
			min_uptime=120
		else
			min_uptime=300
		fi

		## take a nap if necessary
		if (( $uptime < $min_uptime )); then
			let sleep_duration=$min_uptime-$uptime
			log_info "Sequence duration was $uptime seconds (min. allowed $min_uptime s for exit code $return_value)"
			log_info "Sleeping for $sleep_duration s..."

			sleep $sleep_duration
		fi
	fi # "$keepPc" == "off"

	# Sleep inhibited by sleep.lock
	if [ -f sleep.lock ]; then
		keepPc="on"
		sleepLocked=1
	fi

    if [[ "$keepPc" == "off" ]]; then
	    log_info "Option : Keep PC OFF"

	    log_info "Send Yoctopuce To sleep (or not)"
		set +e
	    python -m hypernets.yocto.sleep_monitor
		yocto_sleep=$?
		set -e

		log_info "Yoctosleep status : $yocto_sleep"

		if [[ $yocto_sleep -eq 0 ]]; then
			# All OK, shuttig down
			log_info "Shutting down"
			exit 0
		fi

		# Something went wrong
	    # Cause service exit 1 and doesn't execute SuccessAction=poweroff
		if [[ $yocto_sleep -eq 1 ]]; then
			log_error "Yocto unreachable !!"
		elif [[ $yocto_sleep -eq 255 ]]; then
			log_error "Yocto scheduled wakeup is disabled !!"
			log_error "Waking up is possible ONLY by manually pressing 'WAKE' button !!"
		fi

		log_error "NOT shutting down !!"
	    exit 1
    else
	    log_info "Option : Keep PC ON"

		# Test run
		if [[ "${keepPcInConf-}" == "off" ]]; then
			echo "-----------------------------------"
			echo "keep_pc = off in config_dynamic.ini"
			echo "Automated sequence would have shut down the PC"
			echo
		fi
		if [[ "${startSequenceInConf-}" == "no" ]]; then
			echo "-----------------------------------"
			echo "start_sequence = no in config_dynamic.ini"
			echo "Automated sequence would not have started"
			echo
		fi

		# sleep inhibited by sleep.lock file
		if [[ "${sleepLocked-}" == 1 ]]; then
			log_error "Power off has been inhibited by sleep.lock file in the hypernets_tools folder"
			log_error "Remove the sleep.lock file to enable sending yocto to sleep and powering off the PC"
		fi

	    # Cause systemd service exit 1 and doesn't execute SuccessAction=poweroff
	    exit 1
    fi
}



debug_yocto(){
    # ------------------------------------------------------------------------------
    # YOCTO DEBUG ------------------------------------------------------------------
    # ------------------------------------------------------------------------------
    echo "[DEBUG]  Check if Yocto-Pictor is in (pseudo) deep-sleep mode..."
    set +e
    yoctoState=$(wget -O- \
        'http://127.0.0.1:4444/bySerial/$yoctoPrefix/api/wakeUpMonitor/wakeUpState' \
        2> /dev/null)

    if [[ ! $? -eq 0 ]] ; then
        echo "[DEBUG]  Fail to get Yocto-Pictor wake-up state !"
        return 1
    fi

    echo "[DEBUG]  Yocto-Pictor wake-up state : $yoctoState"

    if [[ $yoctoState == "SLEEPING" ]] ; then
        echo "[DEBUG]  Awaking Yocto-Pictor..."
        yoctoState=$(wget -O- \
            'http://127.0.0.1:4444/bySerial/$yoctoPrefix/api/wakeUpMonitor?wakeUpState=1' \
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

    wget -O- 'http://127.0.0.1:4444/bySerial/$yoctoPrefix/api.txt' > \
        "OTHER/$logNameBase-api.txt" 2> /dev/null

    wget -O- 'http://127.0.0.1:4444/bySerial/$yoctoPrefix/logs.txt' > \
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


## log hypernets_tools repo and branch and root folder
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

	hn_tools_ver=$(python -c "import hypernets; print(hypernets.__version__)")

	echo "[INFO]  Running hypernets_tools version $hn_tools_ver from $hn_tools_repo branch $hn_tools_branch commit $hn_tools_commit"
	echo "[INFO]  hypernets_tools folder is $PWD"
fi
set -e


if [[ "$bypassYocto" != "yes" ]] ; then

    if [[ "$debugYocto" == "yes" ]] ; then
        debug_yocto
    fi

	# Ensure Yocto is online
	set +e
	# check if VirtualHub is running
	systemctl is-active yvirtualhub.service > /dev/null
	if [[ $? -eq 0 ]] ; then
		set -e
		log_info "VirtualHub is running."
	else
		set -e
		log_info "Starting VirtualHub..."
        if [[ "$ID" == "manjaro" ]]; then
		    /usr/bin/VirtualHub &
        elif [[ "$ID" == "debian" ]]; then
            /usr/sbin/VirtualHub &
        else
            log_error "Not able to identify the distribution."
            exit 0
        fi
		sleep 2
		log_info "ok"
	fi

	# Check if yocto is accessible
	set +e
	wget -O- "http://127.0.0.1:4444/bySerial/$yoctoPrefix/api.txt" > /dev/null 2>&1
	retcode=$?
	if [[ $retcode == 0 ]]; then
		log_info "Found Yocto"
		yoctoFW=$(python -m hypernets.yocto.get_FW_ver)
		log_info "$yoctoFW"
	elif [[ $retcode == 8 ]]; then 
		# Server issued an error response. Probably 404 not found.
		log_error "Yocto '$yoctoPrefix' is not accessible !!"

		# list modules if command line API is installed
		if [[ $(command -v YModule) ]]; then
			inventory=$(YModule -r 127.0.0.1 inventory)
			log_error "The list of modules found:"
			echo "$inventory"
		fi

		log_error "Can't do anything without Yocto !!"
		log_error "Exiting the sequence !!"
		exit -1
	else
		# Some other wget error
		log_error "Yocto request finished with error code $retcode"
	fi
	set -e

	# log uptimes
	if [[ $(command -v YModule) ]]; then
		yocto_uptime_millisec=$(YModule -f '[result]' -r 127.0.0.1 $yoctoPrefix get_upTime | awk '{print $1}')
		sys_uptime_sec=$(awk '{print $1}' /proc/uptime)
		log_info "$(printf "yocto uptime is %.1f min, system uptime is %.1f min\n" $(bc -l <<< "$yocto_uptime_millisec / 60000") $(bc -l <<< "$sys_uptime_sec / 60"))"
	fi

	# log supply voltage
	voltage=$(python -m hypernets.yocto.voltage)
	echo "[INFO]  Supply voltage: $voltage V"

	# log wake up reason
	set +e
	wakeupreason=$(python -m hypernets.yocto.wakeupreason)
	set -e
	echo "[INFO]  Wake up reason is : $wakeupreason."

	if [[ "${testRun-}" == "yes" ]] && [[ "$checkWakeUpReason" == "yes" ]] ; then
		echo "[WARNING]  Wake up reason check is disabled for test run. Using standard sequence file $sequence_file"
	elif [[ "$checkWakeUpReason" == "yes" ]] ; then
		if [[ "$wakeupreason" != "SCHEDULE"* ]]; then
			echo "[WARNING]  $wakeupreason is not a reason to start the sequence."
			startSequence="no"
			if [[ "$keepPc" != "on" ]]; then
				log_info "Security sleep 2 minutes..."
				sleep 120
			fi
			shutdown_sequence 0
		fi

		if [[ "$wakeupreason" == "SCHEDULE2" ]]; then
            if [[ ! -n $sequence_file2 ]] ; then
                echo "[WARNING]  No sequence file for Schedule 2 is defined."
                echo "[WARNING]  $sequence_file will be run instead."
            else
                echo "[INFO] $sequence_file2 as alternative sequence file is defined."
                sequence_file=$sequence_file2
            fi 
        fi

		if [[ "$wakeupreason" == "SCHEDULE3" ]]; then
            if [[ ! -n $sequence_file3 ]] ; then
                echo "[WARNING]  No sequence file for Schedule 3 is defined."
                echo "[WARNING]  $sequence_file will be run instead."
            else
                echo "[INFO] $sequence_file3 as alternative sequence file is defined."
                sequence_file=$sequence_file3
            fi 
        fi
	fi # checkWakeUpReason

	if [[ "$checkRain" == "yes" ]] ; then
		log_info "Rain sensor check is enabled."
		log_info "Set relay #4 to ON."
		python -m hypernets.yocto.relay -son -n4
		sleep 5
	fi # checkRain

	# Sync PC clock to yocto gps if more than 5 sec out of sync
	# and yocto gps has fix
	set +e
	utils/sync_clock_to_gps.sh -m 5 -l $numeric_verbosity
	set -e

	# Warn if keep_pc == on and Yocto Watchdog is enabled
	if [[ $(command -v YWakeUpMonitor) ]]; then
		sleep_countdown=$(YWakeUpMonitor -f '[result]' -r 127.0.0.1 $yoctoPrefix get_sleepCountdown)
		if ([[ "${testRun:-}" == "yes" ]] && [[ "$keepPcInConf" == "on" ]] && [[ $sleep_countdown -ne 0 ]]) || \
				([[ "${testRun:-}" != "yes" ]] && [[ "$keepPc" == "on" ]] && [[ $sleep_countdown -ne 0 ]]); then
			log_warning "Shutdown in inhibited by keep_pc = on in config_dynamic.ini, but Yocto watchdog is configured to power off the system!"
		fi
	fi
fi # bypassYocto != yes

if [[ "$startSequence" == "no" ]] ; then
	echo "[INFO]  Start sequence = no"
	if [[ "$keepPc" != "on" ]]; then
		log_info "5 minutes sleep..."
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
	log_info "Set relay #2 to ON."
	python -m hypernets.yocto.relay -son -n2
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
		# 40 - failed to get instrument instance (no hypstar_port device)
		# 88 - rainig
		# 98 - Yocto watchdog timeout is imminent
		if [ $return_value -ne 30 ] && [ $return_value -ne 40 ] && \
				[ $return_value -ne 88 ] && [ $return_value -ne 98 ]; then
			sleep 1
			## VM stabilisation failed
			## power cycle, otherwise the second attempt fails as well
			if [ $return_value -eq 78 ]; then
				echo "[INFO]  Power cycling the radiometer"
				python -m hypernets.yocto.relay -soff -n3
				sleep 10
			fi
			echo "[WARNING]  Second try : "
			set +e
			python3 -m hypernets.open_sequence -f $sequence_file $extra_args
			return_value=$?
		    if [ $return_value -eq 0 ] ; then
		        echo "[INFO]  Success on second attempt"
		    else
				echo "[WARNING]  Hysptar scheduled job on second attempt exited with code $return_value";
			fi
			set -e
		fi
    fi
	shutdown_sequence $return_value
}

trap "exit_actions" EXIT
python3 -m hypernets.open_sequence -f $sequence_file $extra_args
