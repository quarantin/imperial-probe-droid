#!/bin/bash

SLEEP=2
PYTHON='python3'
NAME='Imperial Probe Droid'
IPD='ipd.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	${PYTHON} ${IPD}
	echo "FATAL: ${NAME} just crashed\!"
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
