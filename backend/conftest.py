"""
Pytest configuration for Django tests.
"""
import os
import django
from django.conf import settings

# Set Django settings module if not already set
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()



