#!/bin/bash

function usage {
    echo "Usage: $0 -p <profile> [-c <config>] [-k -t -n]"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -k           : keep the log files"
    echo "  -n           : no debug"
    echo "  -t           : auto terminate"
    exit 1
}

exe=src/patch_generation.py
if [ ! -f $exe ]; then
    echo "Error: $exe not found"
    exit 1
fi

CONFIG="config.yaml"
PROFILE=""
KEEP=0
NO_CONSTRAINT=0
AUTO_TERMINATE=0
while getopts "c:p:dknth" opt; do
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
        n )
            NO_CONSTRAINT=1
            ;;
        t )
            AUTO_TERMINATE=1
            ;;
        h )
            usage
            ;;
        * )
            # omit
            ;;
    esac
done

if [ "$PROFILE" == "sample" ]; then
    echo -e "\033[33mWarning: using sample profile\033[0m"
fi

options="--config $CONFIG --profile $PROFILE"
if [ $KEEP -eq 1 ]; then
    options="$options --keep"
fi
if [ $NO_CONSTRAINT -eq 1 ]; then
    options="$options --no-constraint"
fi

if [ $AUTO_TERMINATE -eq 1 ]; then
    echo exit | python3 $exe $options
    echo ""
else
    python3 $exe $options
fi
