#!/bin/bash

function usage {
    echo "Usage: $0 -p <profile> [-c <config>] [-d -k -b -n -t]"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -d           : dry run, will initialize sandbox"
    echo "  -k           : keep the log files"
    echo "  -b           : build only"
    echo "  -n           : no debug"
    echo "  -t           : auto terminate"
    exit 1
}

exe=src/fix_localization.py

profile="sample"
config="config.yaml"
dry=0
keep=0
build_only=0
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
        d )
            dry=1
            ;;
        k )
            keep=1
            ;;
        b )
            build_only=1
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
if [ $dry -eq 1 ]; then
    options="$options --dry"
fi
if [ $keep -eq 1 ]; then
    options="$options --keep"
fi
if [ $build_only -eq 1 ]; then
    options="$options --build-only"
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
