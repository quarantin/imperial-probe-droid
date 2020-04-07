#!/bin/bash

NAME='IPD Tracker'
MAIN='tracker/tracker.py'
SLEEP=1

./scripts/service.sh "${NAME}" "${MAIN}" "${SLEEP}"
