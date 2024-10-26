#!/bin/bash

function usage {
    echo "Usage: $0 [-c <config>] -p <profile> [-k]"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -p <profile> : specify the profile to run"
    echo "  -k           : keep log"
    exit 1
}

exe=src/validate.py
if [ ! -f $exe ]; then
    echo "Error: $exe not found"
    exit 1
fi

CONFIG="config.yaml"
PROFILE=""
KEEP=0
OPTERR=0  # supress error
while getopts "c:p:kh" opt; do
    case ${opt} in
        c )
            CONFIG=$OPTARG
            ;;
        p )
            PROFILE=$OPTARG
            ;;
        k )
            KEEP=1
            ;;
        h )
            usage
            ;;
        * )
            # omit
            ;;
    esac
done

options="--config $CONFIG --profile $PROFILE"
if [ $KEEP -eq 1 ]; then
    options="$options --keep"
fi

python3 $exe $options
