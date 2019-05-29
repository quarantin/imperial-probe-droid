#!/bin/bash

DATE=$(date '+%Y%m%d-%H%M%S')
mv db.sqlite3 "${DATE}_db.sqlite3"
rm -rf */migrations/
python3 manage.py makemigrations && python3 manage.py migrate --run-syncdb #&& python3 manage.py shell < init.py
