#!/bin/bash

function usage {
    echo "Usage: run_co.sh -p <profile> [-c <config>] [-k -t]"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -k           : keep the log files"
    echo "  -t           : auto terminate"
    exit 1
}

fl=scripts/run_fl.sh
exe=src/chat_only.py

profile="sample"
config="config.yaml"
keep=0
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

bash $fl -p $profile -c $config -d -b -t
if [ $auto -eq 1 ]; then
    echo exit | python3 $exe $options
    echo ""
else
    python3 $exe $options
fi
