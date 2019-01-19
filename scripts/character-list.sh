#!/bin/bash

if [ -z "${1}" ]; then
	echo "Usage: ${0} <ally-code>"
	exit
fi

ALLYCODE="${1}"
URL="https://swgoh.gg/api/player/${ALLYCODE}/"

wget -q -O- "${URL}"  | jq '.units[] | .data | .name' | sed -e 's/^"//' -e 's/"$//' -e 's/\\//g' | sort
