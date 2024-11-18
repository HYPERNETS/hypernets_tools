#!/usr/bin/bash

set -o nounset                              # Treat unset variables as an error
set -euo pipefail                           # Bash Strict Mode

if [[ ${PWD##*/} != "hypernets_tools"* ]]; then
    echo "This script must be run from hypernets_tools folder" 1>&2
    echo "Use : ./utils/${0##*/} instead"
    exit 1
fi

#if [[ "${1-}" == "-h" ]] || [[ "${1-}" == "--help" ]]; then
usage() {
	echo "$0 [-h|--help] [-m max_offset] [-l loglevel]"
	echo
	echo "Sync PC clock to Yocto GPS time"
	echo 
	echo "  -m max_offset   sync only if difference from GPS time is larger than max_offset seconds"
	echo "  -l loglevel     numeric loglevel: 1=ERROR, 2=WARNING, 3=INFO(default), 4=DEBUG"
	echo "  -h, --help      print this help"
	echo
	exit
}
#fi

log_debug() { if [[ $numeric_verbosity -ge 4 ]]; then echo "[DEBUG]  $1"; fi }
log_info() { if [[ $numeric_verbosity -ge 3 ]]; then echo "[INFO]  $1"; fi }
log_warning() { if [[ $numeric_verbosity -ge 2 ]]; then echo "[WARNING]  $1"; fi }
log_error() { if [[ $numeric_verbosity -ge 1 ]]; then echo "[ERROR]  $1"; fi }

set +o nounset

while getopts 'hm:l:' OPTION; do
	case "$OPTION" in
		m) max_offset="$OPTARG" ;;
		l) numeric_verbosity="$OPTARG" ;;
		?|h) usage ;;
	esac
done

# check if loglevel is integer and in allowed range - set to 3=INFO if not
set +eu
[ -n "$numeric_verbosity" ] && [ "$numeric_verbosity" -eq "$numeric_verbosity" ] 2>/dev/null && [ "$numeric_verbosity" -ge 1 ] && [ "$numeric_verbosity" -le 4 ]
if [ $? -ne 0 ]; then
	numeric_verbosity=3
fi
set -eu

# check if max_offset is integer
set +eu
[ -n "$max_offset" ] && [ "$max_offset" -eq "$max_offset" ] 2>/dev/null
if [ $? -ne 0 ]; then
	log_error "$0 -m requires max allowed time offset from GPS in seconds as second parameter."
	exit -1
fi
set -eu

# Check if VirtualHub is running
set +e
systemctl is-active yvirtualhub.service > /dev/null
if [[ $? -ne 0 ]] ; then
	log_error "VirtualHub is not running"
	exit -1
fi

source utils/configparser.sh

# Check if yocto is accessible
yocto=$(parse_config "yocto_prefix2" config_static.ini)
set +e
wget -O- "http://127.0.0.1:4444/bySerial/$yocto/api.txt" > /dev/null 2>&1
retcode=$?
if [[ $retcode == 8 ]]; then 
	# Server issued an error response. Probably 404 not found.
	log_error "Yocto '$yocto' is not accessible !!"
	exit -1
fi
set -e

log_info "Checking if PC clock is within $max_offset s from Yocto GPS"

# check if pc clock is in sync with gps
gps=$(python -m hypernets.yocto.gps | sed -e "s/, /\t/g; s/[()]//g; s/b\?'//g")
gps_datetime=$(cut -f 3 <<< $gps)

if [[ "$gps_datetime" != "N/A" ]] && [[ "$gps_datetime" != "" ]]; then 
	# gps has fix
	sys_timestamp=$(date -u +%s)
	gps_timestamp=$(date -d "$gps_datetime UTC" -u +%s)
	delta=$(( sys_timestamp - gps_timestamp ))

	# Sync PC clock to yocto GPS if absolute difference is over $max_offset seconds
	if [[ "${delta#-}" -gt "$max_offset" ]]; then
		echo "[WARNING] PC clock is not synced with Yocto GPS"
		echo "[WARNING] Yocto GPS time: $gps_datetime UTC"
		echo "[WARNING] PC time:        $(date -u -d @$sys_timestamp '+%Y/%m/%d %H:%M:%S') UTC"
		echo "[WARNING] Syncing PC clock to Yocto GPS"

		# check if ntp is enabled and disable if it is, 
		# otherwise timedatectl won't allow setting the time
		ntp_enabled=$(timedatectl show -p NTP --value)
		if [[ "$ntp_enabled" == "yes" ]]; then
			timedatectl --no-ask-password --no-pager set-ntp 0
		fi

		# make new timedate in local time zone without -u since timedatect set-time uses local time zone
		new_timedate=$(date -d @$gps_timestamp '+%Y-%m-%d %H:%M:%S')
		timedatectl --no-ask-password --no-pager set-time "$new_timedate" > /dev/null

		# re-enable ntp if it was enabled before
		if [[ "$ntp_enabled" == "yes" ]]; then
			timedatectl --no-ask-password --no-pager set-ntp 1
		fi

		# print the pc and yocto gps times after sync
		gps=$(python -m hypernets.yocto.gps | sed -e "s/, /\t/g; s/[()]//g; s/b\?'//g")
		gps_datetime=$(cut -f 3 <<< $gps)
		sys_timestamp=$(date -u +%s)
		gps_timestamp=$(date -d "$gps_datetime UTC" -u +%s)
		echo "[WARNING] After syncing PC clock"
		echo "[WARNING] Yocto GPS time: $gps_datetime UTC"
		echo "[WARNING] PC time:        $(date -u -d @$sys_timestamp '+%Y/%m/%d %H:%M:%S') UTC"
	else 
		log_info "PC clock is within $max_offset seconds from Yocto GPS time"
	fi
else
	log_info "No GPS time available from Yocto"
fi

