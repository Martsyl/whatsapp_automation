# your_project/celery.py
# Place this file next to settings.py (same folder as manage.py)

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_admin.settings')

app = Celery('django_admin')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()