#!/bin/bash

function usage {
    echo "Usage: run.sh -p <profile> [-c <config>] [-k -n -t]"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -d           : dry run, will initialize sandbox"
    echo "  -k           : keep the log files"
    echo "  -n           : no debug"
    echo "  -t           : auto terminate"
    exit 1
}

fl=scripts/run_fl.sh
pg=scripts/run_pg.sh
vd=scripts/run_vd.sh

profile="sample"
config="config.yaml"
keep=0
no_dbg=0
auto=0
while getopts "p:c:knth" opt; do
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
            usage
            ;;
    esac
done

options="-c $config -p $profile"
if [ $keep -eq 1 ]; then
    options="$options -k"
fi
if [ $no_dbg -eq 1 ]; then
    options="$options -n"
fi
if [ $auto -eq 1 ]; then
    options="$options -t"
fi

echo -e "\033[36mOptions: $options\033[0m"

echo -e "\033[33mCleansing previous logs...\033[0m"
rm -rf *.log *.json

echo -e "\033[36mRunning Fix Localization\033[0m"
bash $fl $options -d
if [ $? -ne 0 ]; then
    echo -e "\033[31mFix Localization failed\033[0m"
    exit 1
fi

echo -e "\033[36mRunning Patch Generation\033[0m"
bash $pg $options
if [ $? -ne 0 ]; then
    echo -e "\033[31mPatch Generation failed\033[0m"
    exit 1
fi

echo -e "\033[36mRunning Validation\033[0m"
bash $vd $options
if [ $? -ne 0 ]; then
    echo -e "\033[31mValidation failed\033[0m"
    exit 1
fi