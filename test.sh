#!/bin/bash

cd src

# get all .py files under current directory
files=$(find tests -name "*.py")
for file in $files
do
    echo -e "\e[33m>>>>>>>>>> Running $file\e[0m"
    # remove .py extension and replace / with .
    file=$(echo $file | sed 's/\//\./g' | sed 's/\.py//g')
    python -m $file
    if [ $? -ne 0 ]; then
        echo -e "\e[31m>>>>>>>>>> $file failed\e[0m"
        exit 1
    else
        echo -e "\e[32m>>>>>>>>>> $file passed\e[0m"
    fi
    echo ""
done
