#!/bin/bash

DATE=$(date '+%Y%m%d-%H%M%S')
mv db.sqlite3 "${DATE}_db.sqlite3"
rm -rf */migrations/
python manage.py makemigrations && python manage.py migrate --run-syncdb #&& python manage.py shell < init.py
