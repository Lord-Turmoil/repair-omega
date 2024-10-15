#!/bin/bash

# Simple wrapper for run.sh

run=scripts/run.sh

profile=${1:-sample}

time bash $run -k -t -p $profile
