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

CONFIG_NAME=config.json
LOCAL_CONFIG_DIR=.
REMOTE_CONFIG_DIR=~/imperial-probe-droid.git

LOCAL_PATH=${LOCAL_CONFIG_DIR}/${CONFIG_NAME}
REMOTE_PATH=${USER}@${SERVER}:${REMOTE_CONFIG_DIR}/${CONFIG_NAME}

TMP_LOCAL_PATH=/tmp/local-${CONFIG_NAME}
TMP_REMOTE_PATH=/tmp/remote-${CONFIG_NAME}

cp "${LOCAL_PATH}" "${TMP_LOCAL_PATH}"
rsync -ave "ssh -p ${PORT}" "${REMOTE_PATH}" "${TMP_REMOTE_PATH}"

cp "${TMP_LOCAL_PATH}" "${TMP_LOCAL_PATH}.orig"
cp "${TMP_REMOTE_PATH}" "${TMP_REMOTE_PATH}.orig"

vimdiff "${TMP_LOCAL_PATH}" "${TMP_REMOTE_PATH}"

DIFF_LOCAL=$(diff "${TMP_LOCAL_PATH}" "${TMP_LOCAL_PATH}.orig")
DIFF_LOCAL_STATUS=$?
DIFF_REMOTE=$(diff "${TMP_REMOTE_PATH}" "${TMP_REMOTE_PATH}.orig")
DIFF_REMOTE_STATUS=$?

LOCAL_TARGET="${LOCAL_CONFIG_DIR}/${CONFIG_NAME}"
if [ "${DIFF_LOCAL_STATUS}" -ne "0" ]; then
	echo "Replacing ${LOCAL_TARGET}"
	cp "${TMP_LOCAL_PATH}" "${LOCAL_TARGET}"
else
	echo "Keeping ${LOCAL_TARGET}"
fi

REMOTE_TARGET="${USER}@${SERVER}:${REMOTE_CONFIG_DIR}/${CONFIG_NAME}"
if [ "${DIFF_REMOTE_STATUS}" -ne "0" ]; then
	echo "Replacing ${REMOTE_TARGET}"
	rsync -ave "ssh -p ${PORT}" "${TMP_REMOTE_PATH}" "${REMOTE_TARGET}"
else
	echo "Keeping ${REMOTE_TARGET}"
fi
