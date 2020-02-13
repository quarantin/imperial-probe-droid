#!/bin/bash

SLEEP=1
ERROR='error.log'
OUTPUT='output.log'
NAME='Imperial Probe Droid'
IPD='ipd.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	(unbuffer python ${IPD} | tee -a "${OUTPUT}") 3>&1 1>&2 2>&3 | tee -a "${ERROR}"
	if [ "${?}" -ne "0" ]; then
		echo "FATAL: ${NAME} just crashed\!"
	fi
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
