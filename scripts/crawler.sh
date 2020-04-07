#!/bin/bash

NAME='IPD Crawler'
MAIN='crawler/crawler.py'
SLEEP=1

./scripts/service.sh "${NAME}" "${MAIN}" "${SLEEP}"
