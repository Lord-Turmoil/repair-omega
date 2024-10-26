#!/bin/bash

function usage() {
    echo "Usage: $0 -p <profile>"
    exit 1
}

exe=src/build.py
if [ ! -f $exe ]; then
    echo "Error: $exe not found"
    exit 1
fi


PROFILE=""
while getopts "p:h" opt; do
    case $opt in
        p)
            PROFILE=$OPTARG
            ;;
        h)
            usage
            ;;
        * )
            # omit
            ;;
    esac
done

if [ -z "$PROFILE" ]; then
    usage
    exit 1
fi

python3 $exe -p $PROFILE
