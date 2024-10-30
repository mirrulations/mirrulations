#!/bin/bash

WORK_DIR="/home/cs334/mirrulations/scripts/"
LOG_FILE=/var/log/mirrulations_counts.log
START_TIME=$(date -Iseconds)

echo "$START_TIME: Running" >> $LOG_FILE
cd $WORK_DIR
source .venv/bin/python3/activate

./get_counts.py -o "/tmp/mirrulations_$START_TIME.json" redis 2>> $LOG_FILE &&
    ./correct_counts.py -i "/tmp/mirrulations_$START_TIME.json" -o "/tmp/mirrulations_${START_TIME}_corrected.json" 2>> $LOG_FILE &&
    ./set_counts.py -y -i "/tmp/mirrulations_${START_TIME}_corrected.json" 2>> $LOG_FILE

rm -f "/tmp/mirrulations_${START_TIME}_corrected.json" "/tmp/mirrulations_$START_TIME.json"
