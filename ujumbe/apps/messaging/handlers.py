import json
import logging

import africastalking
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from .models import Message

logger = logging.getLogger(__name__)


class TelecomHandler(object):
    @staticmethod
    def send_sms(phonenumber, text):
        raise NotImplementedError


class Telerivet(TelecomHandler):
    @staticmethod
    def send_sms(phonenumber, text):
        url = "https://api.telerivet.com/v1/projects/{}/messages/send".format(settings.TELERIVET_PROJECT_ID)
        data = {
            "content": text,
            "to_number": phonenumber
        }
        headers = {
            "Content-Type": "application/json"
        }
        _response = requests.post(url=url, data=json.dumps(data), headers=headers,
                                  auth=HTTPBasicAuth(settings.TELERIVET_API_KEY, ''))
        logger.debug("Telerivet Response {}".format( _response.text))
        if _response.ok:
            response = _response.json()
            return {
                "handler": Message.MessageProviders.Telerivet,
                "delivery_status": response["status"],
                "provider_id": response["id"],
                "cost": settings.TELERIVET_SMS_SEND_COST,
                "currency_code": settings.TELERIVET_SMS_SEND_CURRENCY,
            }
        else:
            _response.raise_for_status()


class Africastalking(TelecomHandler):
    @staticmethod
    def send_sms(phonenumber, text):
        africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        sms = africastalking.SMS
        response = sms.send(text, [phonenumber, ], )
        logger.debug("Africastalking reponse {}".format(str(response)))
        message_data = response["SMSMessageData"]["Recipients"][0]  # only one recipient
        status_code = message_data["statusCode"]
        cost_str_parts = str(message_data["cost"]).split(" ")

        return {
            "handler": Message.MessageProviders.Africastalking,
            "delivery_status": message_data["status"],
            "provider_id": message_data["messageId"],
            "cost": cost_str_parts[1],
            "currency_code": cost_str_parts[0],
        }
