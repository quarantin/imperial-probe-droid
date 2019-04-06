#!/bin/bash

URL="https://swgoh.gg/api/characters/"

wget -q -O- "${URL}" | jq '.[].name' | sed -e 's/\\"/"/g' -e 's/^"//' -e 's/"$//'
