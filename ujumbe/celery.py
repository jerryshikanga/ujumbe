import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ujumbe.settings.custom')

app = Celery('ujumbe')

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
