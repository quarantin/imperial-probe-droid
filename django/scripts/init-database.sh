#!/bin/bash

rm -f db.sqlite3
rm -rf */migrations/
python3 manage.py makemigrations && python3 manage.py migrate --run-syncdb && python3 manage.py shell < init.py
