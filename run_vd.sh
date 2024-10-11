#!/bin/bash

function usage {
    echo "Usage: run_v.sh -p <profile>"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    exit 1
}

exe=src/validate.py

profile="sample"
while getopts "p:c:dkbnth" opt; do
    case ${opt} in
        p )
            profile=$OPTARG
            ;;
        h )
            usage
            ;;
        \? )
            # omit
            ;;
    esac
done

if [ "$profile" == "sample" ]; then
    echo -e "\033[33mWarning: using sample profile\033[0m"
fi

options="--profile $profile"
python3 $exe $options
