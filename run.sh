#!/bin/bash

function usage {
    echo "Usage: run.sh -p <profile> -c <config> -d -k"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -d           : dry run, will initialize sandbox"
    echo "  -k           : keep the log files"
    exit 1
}

profile="sample"
config="config.yaml"
dry=0
keep=0
while getopts "p:c:dkh" opt; do
    case ${opt} in
        p )
            profile=$OPTARG
            ;;
        c )
            config=$OPTARG
            ;;
        d )
            dry=1
            ;;
        k )
            keep=1
            ;;
        h )
            usage
            ;;
        \? )
            usage
            ;;
    esac
done

if [ "$profile" == "sample" ]; then
    echo -e "\033[33mWarning: using sample profile\033[0m"
fi

options="--config $config --profile $profile"
if [ $dry -eq 1 ]; then
    options="$options --dry"
fi
if [ $keep -eq 1 ]; then
    options="$options --keep"
fi

python3 src/main.py $options
