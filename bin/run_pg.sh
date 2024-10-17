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

profile="sample"
config="config.yaml"
keep=0
no_dbg=0
auto=0
while getopts "p:c:dkbnth" opt; do
    case ${opt} in
        p )
            profile=$OPTARG
            ;;
        c )
            config=$OPTARG
            ;;
        k )
            keep=1
            ;;
        n )
            no_dbg=1
            ;;
        t )
            auto=1
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

options="--config $config --profile $profile"
if [ $keep -eq 1 ]; then
    options="$options --keep"
fi
if [ $no_dbg -eq 1 ]; then
    options="$options --no-debug"
fi

if [ $auto -eq 1 ]; then
    echo exit | python3 $exe $options
    echo ""
else
    python3 $exe $options
fi
