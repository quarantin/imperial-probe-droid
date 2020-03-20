#!/bin/bash

SLEEP=1
ERROR='logs/crawler-error.log'
OUTPUT='logs/crawler-output.log'
NAME='IPD Crawler'
MAIN='crawler/crawler.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	(PYTHONPATH=.:$PYTHONPATH unbuffer python ${MAIN} | tee -a "${OUTPUT}") 3>&1 1>&2 2>&3 | tee -a "${ERROR}"
	if [ "${?}" -ne "0" ]; then
		echo "FATAL: ${NAME} just crashed\!"
	fi
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
