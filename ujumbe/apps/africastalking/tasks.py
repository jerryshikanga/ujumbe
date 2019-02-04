import logging

from celery import task
from django.db import transaction

from ujumbe.apps.africastalking.models import IncomingMessage
from ujumbe.apps.profiles.tasks import send_bulk_sms

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    with transaction.atomic():
        responses = []
        for message in IncomingMessage.objects.select_for_update().filter(processed=False):
            try:
                message.process()
                responses.append({
                    "phonenumber": message.phonenumber,
                    "text": message.response
                })
            except Exception as e:
                logger.error(str(e))
        send_bulk_sms.delay(responses)
