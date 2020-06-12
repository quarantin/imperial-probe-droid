#!/bin/bash

USER="${1}"
SERVER="${2}"
PORT="${3}"

if [ -z "${PORT}" ]; then
	PORT=22
fi

if [ -z "${USER}" ] | [ -z "${SERVER}" ]; then
	echo "User: ${0} <user> <server> [port]"
	exit 1
fi

for module in swgoh grandarena territorybattle territorywar; do
	scp -P "${PORT}" "${USER}@${SERVER}:ipd/${module}/migrations/0*.py" "./${module}/migrations/"
done
