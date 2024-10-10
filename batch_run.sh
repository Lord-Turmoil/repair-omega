#!/bin/bash

function usage {
    echo "Usage: batch_run.sh -p <profile> -c <config>"
    echo "  -p <profile> : specify the profile to run (default is sample)"
    echo "  -c <config>  : specify the config file to use (default is config.yaml)"
    echo "This require there are two profiles: <profile> and <profile>-c"
    echo "And the profile in argument should be <profile> without .json"
    exit 1
}

profile="sample"
config="config.yaml"
while getopts "p:c:h" opt; do
    case ${opt} in
        p )
            profile=$OPTARG
            ;;
        c )
            config=$OPTARG
            ;;
        h )
            usage
            ;;
        \? )
            usage
            ;;
    esac
done

options_base="-c $config -k -t"

# build only
echo -e "\033[36m>>>>> Build Only\033[0m"
options="$options_base -p $profile -d -b"
./run.sh $options
if [ $? -ne 0 ]; then
    echo "Error: build_only failed"
    exit 1
fi
echo ""

# constraint + debug
echo -e "\033[36m>>>>> Preset: Constraint + Debug\033[0m"
options="$options_base -p ${profile}-c"
./run.sh $options
echo ""

# debug
echo -e "\033[36m>>>>> Preset: Debug\033[0m"
options="$options_base -p $profile"
./run.sh $options
echo ""

# constraint
echo -e "\033[36m>>>>> Preset: Constraint\033[0m"
options="$options_base -p ${profile}-c -n"
./run.sh $options
echo ""

# nothing
echo -e "\033[36m>>>>> Preset: Nothing\033[0m"
options="$options_base -p ${profile} -n"
./run.sh $options
echo ""
