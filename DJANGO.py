import os, sys

import django
from django.conf import settings

sys.path.append("django/")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swgoh.settings')
django.setup()
