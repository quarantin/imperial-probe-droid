#!/bin/bash

SLEEP=1
ERROR='tracker-error.log'
OUTPUT='tracker-output.log'
NAME='IPD Tracker'
MAIN='tracker/tracker.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	(PYTHONPATH=.:$PYTHONPATH unbuffer python ${MAIN} | tee -a "${OUTPUT}") 3>&1 1>&2 2>&3 | tee -a "${ERROR}"
	if [ "${?}" -ne "0" ]; then
		echo "FATAL: ${NAME} just crashed\!"
	fi
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
