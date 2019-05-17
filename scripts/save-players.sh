#!/bin/bash

(echo 'drop table swgoh_player;'; sqlite3 ./django/db.sqlite3 '.dump swgoh_player') > ./cache/players.sql
