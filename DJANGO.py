import os, sys

import django
from django.conf import settings

sys.path.append("django/")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avatars.settings')
django.setup()
