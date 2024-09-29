#!/bin/bash

if [ -z "$1" ]; then
    echo -e "\033[33mWarning: using sample profile\033[0m"
fi

profile=${1:-"sample"}
python3 src/main.py         \
    --config config.yaml    \
    --profile $profile
