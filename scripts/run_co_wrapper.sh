#!/bin/bash

# Simple wrapper for run_co.sh

run=scripts/run_co.sh

profile=${1:-sample}

time bash $run -k -t -p $profile
