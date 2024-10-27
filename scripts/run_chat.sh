#!/bin/bash

function usage() {
    echo "Usage: $0 [-c <config>] -p <profile> [-k -n]"
    echo "-c <config>  : specify the config file to use (default is config.yaml)"
    echo "-p <profile> : specify the profile to run"
    echo "-k           : keep the log files"
    echo "-n           : no constraint"
}

function output_duration() {
    end=`date +%s`
    runtime=$((end-start))
    echo "Time elapsed: $runtime seconds"
}

function run() {
    echo -e "\033[36mRunning Path Generation (Chat Only)\033[0m"
    bash $co $options -t
    if [ $? -ne 0 ]; then
        echo -e "\033[31mFix Localization failed\033[0m"
        exit 1
    fi

    echo -e "\033[36mRunning Validation\033[0m"
    bash $vd $options
    if [ $? -ne 0 ]; then
        echo -e "\033[31mValidation failed\033[0m"
        exit 1
    fi
}

function validate() {
    result_file="validate.lock"
    result=$(cat $result_file 2> /dev/null)
    if [ "$result" == "valid" ]; then
        echo -e "\033[32mSucceeded!\033[0m"
        output_duration
        exit 0
    elif [ "$result" == "invalid" ]; then
        echo -e "\033[33mFailed\033[0m"
    else
        echo -e "\033[33mUnknown error, aborted\033[0m"
        exit 1
    fi
}

# Check if required files exist
co=bin/run_co.sh
vd=bin/run_vd.sh

if [ ! -f $co ]; then
    echo "Error: $co not found"
    exit 1
fi
if [ ! -f $vd ]; then
    echo "Error: $vd not found"
    exit 1
fi

# Parse arguments
CONFIG="config.yaml"
PROFILE=""
KEEP=0
NO_CONSTRAINT=0
while getopts "c:p:knh" opt; do
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
    esac
done

if [ -z "$PROFILE" ]; then
    usage
    exit 1
fi

options="-c $CONFIG -p $PROFILE"
if [ $KEEP -eq 1 ]; then
    options="$options -k"
fi
if [ $NO_CONSTRAINT -eq 1 ]; then
    options="$options -n"
fi

echo -e "\033[35mRepair with chat-only\033[0m"
echo -e "\033[36mProfile: $PROFILE\033[0m"
echo -e "\033[36mOptions: $options\033[0m"

echo -e "\033[33mCleansing previous logs...\033[0m"
rm -rf *.log *.json

start=`date +%s`

echo -e "\033[33mPreparing workspace\033[0m"
exe=bin/build.sh
if [ ! -f $exe ]; then
    echo "Error: $exe not found"
    exit 1
fi
bash $exe -p $PROFILE

run
validate
