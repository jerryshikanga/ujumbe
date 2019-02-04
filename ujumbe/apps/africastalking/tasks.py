import logging

from celery import task

from ujumbe.apps.africastalking.models import IncomingMessage
from ujumbe.apps.profiles.tasks import send_bulk_sms

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    responses = IncomingMessage.process_pending_messages()
    if len(responses) > 0:
        send_bulk_sms.delay(responses)
    return responses
