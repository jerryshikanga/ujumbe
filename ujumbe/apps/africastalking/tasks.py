import logging

from celery import task

from ujumbe.apps.africastalking.models import IncomingMessage
from ujumbe.apps.profiles.tasks import send_bulk_sms

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    responses = []
    for message in IncomingMessage.objects.filter(processed=False):
        try:
            response = message.process()
            if response is not None:
                responses.append({
                    "phonenumber": message.phonenumber,
                    "text": response
                })
        except Exception as e:
            logger.error(str(e))
    if len(responses) > 0:
        send_bulk_sms.delay(responses)
