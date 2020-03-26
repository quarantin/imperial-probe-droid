#!/bin/bash

SLEEP=1
NAME='IPD Crawler'
MAIN='crawler/crawler.py'

while true; do
	echo "INFO: Starting ${NAME}..."
	PYTHONPATH=.:$PYTHONPATH python ${MAIN}
	if [ "${?}" -ne "0" ]; then
		echo "FATAL: ${NAME} just crashed\!"
	fi
	echo "INFO: Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
