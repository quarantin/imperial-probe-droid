#!/bin/bash

ALLY_CODE=$(cat ally-code.txt)
if [ -n "${1}" ]; then
	ALLY_CODE="${1}"
fi

wget -q -O- swgoh.gg/api/players/${ALLY_CODE}/mods/ | python3 -m json.tool | less
