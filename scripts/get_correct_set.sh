#!/bin/bash

WORK_DIR="/home/cs334/mirrulations/scripts/"
LOG_FILE=/var/log/mirrulations_counts.log
START_TIME=$(date -u -Iseconds)
echo "$START_TIME: RUnning" > $LOG_FILE
cd $WORK_DIR

PYTHON=".venv/bin/python3"

$PYTHON get_counts redis -o "/tmp/mirrulations_$START_TIME.json" 2>> $LOG_FILE &&
    $PYTHON correct_counts -i "/tmp/mirrulations_$START_TIME.json" -o "/tmp/mirrulations_${START_TIME}_corrected.json" 2>> $LOG_FILE &&
    $PYTHON set_counts -y -i "/tmp/mirrulations_${START_TIME}_corrected.json" 2>> $LOG_FILE

rm "/tmp/mirrulations_${START_TIME}_corrected.json" "/tmp/mirrulations_$START_TIME.json"
