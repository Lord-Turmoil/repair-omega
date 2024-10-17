#!/bin/bash

# Run:
#   Prepare project for debug

profile=${1:?"Usage: $0 <profile>"}
options="-p $profile -d -b"

echo -e "\033[36mPreparing sandbox\033[0m"
bash bin/run_fl.sh $options
