#!/bin/bash

run=scripts/run.sh

profile=${1:-sample}

time bash $run -k -t -p $profile
