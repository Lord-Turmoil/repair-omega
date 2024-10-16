#!/bin/bash

# Run:
#   Build project with dry run
#   Chat only fix
#   Patch validation

function usage {
    echo "Usage: run_co.sh -p <profile> [-c <config>] [-k -t]"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "  -k           : keep the log files"
    echo "  -t           : auto terminate"
    exit 1
}

fl=scripts/run_fl.sh
vd=scripts/run_vd.sh
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

echo -e "\033[36mOptions: $options\033[0m"

echo -e "\033[33mCleansing previous logs...\033[0m"
rm -rf *.log *.json

echo -e "\033[36mPreparing sandbox\033[0m"
bash $fl -p $profile -c $config -d -b -t

echo -e "\033[36mRunning Patch Generation (Chat Only)\033[0m"
if [ $auto -eq 1 ]; then
    echo exit | python3 $exe $options
    echo ""
else
    python3 $exe $options
fi

echo -e "\033[36mRunning Validation\033[0m"
bash $vd -p $profile
if [ $? -ne 0 ]; then
    echo -e "\033[31mValidation failed\033[0m"
    exit 1
fi