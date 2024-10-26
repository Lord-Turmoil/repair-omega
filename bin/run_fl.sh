#!/bin/bash

function usage {
    echo "Usage: $0 [-c <config>] -p <profile>  [-k -t -n]"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -p <profile> : specify the profile to run"
    echo "  -k           : keep the log files"
    echo "  -t           : auto terminate"
    echo "  -n           : disable constraint"
    echo "  -r           : rerun"
    exit 1
}

exe=src/fix_localization.py
if [ ! -f $exe ]; then
    echo "Error: $exe not found"
    exit 1
fi

CONFIG="config.yaml"
PROFILE=""
KEEP=0
AUTO_TERMINATE=0
NO_CONSTRAINT=0
RERUN=0
while getopts "c:p:ktnrh" opt; do
    case $opt in
        c)
            CONFIG=$OPTARG
            ;;
        p)
            PROFILE=$OPTARG
            ;;
        k)
            KEEP=1
            ;;
        t)
            AUTO_TERMINATE=1
            ;;
        n)
            NO_CONSTRAINT=1
            ;;
        r )
            RERUN=1
            ;;
        h)
            usage
            ;;
        * )
            # omit
            ;;
    esac
done

if [ -z "$PROFILE" ]; then
    usage
    exit 1
fi

options="--config $CONFIG --profile $PROFILE"
if [ $KEEP -eq 1 ]; then
    options="$options --keep"
fi
if [ $NO_CONSTRAINT -eq 1 ]; then
    options="$options --no-constraint"
fi
if [ $RERUN -eq 1 ]; then
    options="$options --rerun"
fi

if [ $AUTO_TERMINATE -eq 1 ]; then
    echo exit | python3 $exe $options
    echo ""
else
    python3 $exe $options
fi
