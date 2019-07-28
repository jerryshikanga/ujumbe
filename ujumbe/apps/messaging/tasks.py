import logging

import requests
from bs4 import BeautifulSoup

from celery import task
from django.conf import settings
from django.db import transaction

from ujumbe.apps.messaging.models import IncomingMessage
from .models import OutgoingMessages

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    with transaction.atomic():
        messages = IncomingMessage.objects.select_for_update().filter(processed=False)
        for message in messages:
            message.process()


@task
def process_outgoing_messages():
    with transaction.atomic():
        messages = OutgoingMessages.objects.select_for_update().filter(processed=False)
        for message in messages:
            message.process()


def translate_text(source: str, destination: str, text):
    params = {
        "text": text,
        "lang": "%s-%s" % (source, destination),
        "format": "text",
        "key": settings.YANDEX_TRANSLATE_API_KEY
    }
    response = requests.get(settings.YANDEX_TRANSLATE_API_URL, params)
    soup = BeautifulSoup(response.text, features="xml")
    return soup.find("text").string


@task
def send_sms_async(message_id: int):
    message = OutgoingMessages.objects.get(id=message_id)
    message.send()
