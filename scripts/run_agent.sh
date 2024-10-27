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
    retry=$1
    run_options=""
    prefix=""
    if [ $retry -eq 1 ]; then
        run_options="$run_options -r"
        prefix="(Re) "
    fi
    echo -e "\033[36m${prefix}Running Fix Localization\033[0m"
    bash $fl $options $run_options
    if [ $? -ne 0 ]; then
        echo -e "\033[31mFix Localization failed\033[0m"
        exit 1
    fi

    echo -e "\033[36m${prefix}Running Patch Generation\033[0m"
    bash $pg $options
    if [ $? -ne 0 ]; then
        echo -e "\033[31mPatch Generation failed\033[0m"
        exit 1
    fi

    echo -e "\033[36m${prefix}Running Validation\033[0m"
    bash $vd $options
    if [ $? -ne 0 ]; then
        echo -e "\033[31mValidation failed\033[0m"
        exit 1
    fi
}

function validate() {
    retry=$1

    result_file="validate.lock"
    result=$(cat $result_file 2> /dev/null)
    if [ "$result" == "valid" ]; then
        echo -e "\033[32mSucceeded!\033[0m"
        output_duration
        exit 0
    elif [ "$result" == "invalid" ]; then
        if [ $retry -eq 1 ]; then
            echo -e "\033[31mFailed after second try\033[0m"
        else
            echo -e "\033[33mFailed, attempt to retry\033[0m"
        fi
    else
        echo -e "\033[33mUnknown error, aborted\033[0m"
        exit 1
    fi
}

# Check if required files exist
fl=bin/run_fl.sh
pg=bin/run_pg.sh
vd=bin/run_vd.sh

if [ ! -f $fl ]; then
    echo "Error: $fl not found"
    exit 1
fi
if [ ! -f $pg ]; then
    echo "Error: $pg not found"
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

options="-c $CONFIG -p $PROFILE -t"
if [ $KEEP -eq 1 ]; then
    options="$options -k"
fi
if [ $NO_CONSTRAINT -eq 1 ]; then
    options="$options -n"
fi

echo -e "\033[35mRepair with agent\033[0m"
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

echo -e "\033[36m========== First Try ==========\033[0m"
run 0
validate 0

echo -e "\033[36m========= Second Try ==========\033[0m"
run 1
validate 1
