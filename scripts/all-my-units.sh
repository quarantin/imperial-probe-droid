#!/bin/bash

ALLY_CODE=$(cat ally-code.txt)
if [ -n "${1}" ]; then
	ALLY_CODE="${1}"
fi

wget -q -O- swgoh.gg/api/player/${ALLY_CODE}/ | python -m json.tool | less
