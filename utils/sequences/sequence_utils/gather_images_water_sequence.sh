#!/usr/bin/bash

set -o nounset 
set -euo pipefail


function usage(){
	printf "\nPurpose : copy and prefix files from water SEQ according to their\n"
	printf "          'position name'\n\n"

	printf "example : 01_006_0090_2_0140.jpg from the folder SEQ20210609T093031\n"
	printf "          will be copied with the name SK1_SEQ20210609T093031.jpg\n"
	printf "          as it corresponds to the pointing to the sky position 1\n"
	printf "          in the standard water protocol.\n\n"

	printf "Note : prefix are chosen as follow : IR1, SK1, WAT, SK2, IR2, SUN\n\n"

	printf "Usage : %s /path/to/DATA output_dir false\n" "$0"
	printf "         - only display the output files (test purpose)\n\n"
	printf "        %s /path/to/DATA output_dir true\n" "$0"
	printf "         - will create the folder and copy all files matches\n\n"
	exit 0
}

function find_and_prefix_and_copy(){
    data_dir=$1
    filetype=$2
    prefix=$3
    dir_output=$4
    copy=$5

    for f in $(find $data_dir -name $filetype); do
		# Extract SEQ name
		filename=$(echo $f | rev | cut -d"/" -f3 | rev)
		echo "$dir_output/$prefix$filename.jpg"
		if [ $copy == true ]; then
			cp "$f" "$dir_output/$prefix$filename.jpg"
		fi
    done
}

function copy_by_definition(){
    data_dir=$1
    dir_output=$2
    copy=$3
    
	if [ -z $copy ]; then
		echo "Error : you have to provide a copy mode (true/false)"
		return 1
	fi

    if [ $copy = true ]; then
    	mkdir -p "$dir_output"
    fi

    find_and_prefix_and_copy $data_dir "01_003_0090_2_0180.jpg" "IR1_" $dir_output $copy
    find_and_prefix_and_copy $data_dir "01_006_0090_2_0140.jpg" "SK1_" $dir_output $copy
    find_and_prefix_and_copy $data_dir "01_009_0090_2_0040.jpg" "WAT_" $dir_output $copy
    find_and_prefix_and_copy $data_dir "01_012_0090_2_0140.jpg" "SK2_" $dir_output $copy
    find_and_prefix_and_copy $data_dir "01_015_0090_2_0180.jpg" "IR2_" $dir_output $copy
    find_and_prefix_and_copy $data_dir "01_016_-001_2_-001.jpg" "SUN_" $dir_output $copy
}

set +o nounset

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] ; then usage; fi
copy_by_definition $1 $2 $3
