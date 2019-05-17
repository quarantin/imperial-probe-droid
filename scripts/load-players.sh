#!/bin/bash

sqlite3 ./django/db.sqlite3 < ./cache/players.sql

