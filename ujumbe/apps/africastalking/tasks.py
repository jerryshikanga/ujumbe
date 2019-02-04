import logging

from celery import task
from django.db import transaction

from ujumbe.apps.africastalking.models import IncomingMessage

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    with transaction.atomic():
        for message in IncomingMessage.objects.select_for_update().filter(processed=False):
            message.process()
