#!/bin/bash

NAME="${1}"
MAIN="${2}"
SLEEP="${3:-1}"

if [ -z "${NAME}" ] | [ -z "${MAIN}" ]; then
	echo "Usage: ${0} \"Service Name\" \"path/to/main.py\""
	exit -1
fi

. ENV/bin/activate

while true; do
	echo "Starting ${NAME}..."
	PYTHONPATH=.:$PYTHONPATH python ${MAIN}
	if [ "${?}" -ne "0" ]; then
		echo "ERROR: ${NAME} just crashed\!"
	fi
	echo "Restarting ${NAME} in ${SLEEP} seconds..."
	sleep ${SLEEP}
done
