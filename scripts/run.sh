#!/bin/bash

SLEEP=1
PYTHON='python3'
NAME='Imperial Probe Droid'
IPD='ipd.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	${PYTHON} ${IPD}
	if [ "${?}" -ne "0" ]; then
		echo "FATAL: ${NAME} just crashed\!"
	fi
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
