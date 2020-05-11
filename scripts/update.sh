#!/bin/bash -x
set -e

BRANCH=master
if ! [ -z "${1}" ]; then
        BRANCH="${1}"
fi

git checkout "${BRANCH}"
git fetch
git pull

set +x
. ENV/bin/activate
set -x

pip install -r requirements.txt | grep -v '^Requirement already satisfied'
python manage.py makemigrations && python manage.py migrate
python manage.py collectstatic
