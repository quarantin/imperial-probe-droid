#!/bin/bash

. ENV/bin/activate

python manage.py ${@}
