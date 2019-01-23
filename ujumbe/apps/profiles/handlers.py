import json

import telerivet
import africastalking
from django.conf import settings

from ujumbe.apps.africastalking.models import Message


class TelecomHandler(object):
    @staticmethod
    def send_sms(self, phonenumber, text):
        raise NotImplementedError


class Telerivet(TelecomHandler):
    @staticmethod
    def send_sms(self, phonenumber, text):
        tr = telerivet.API(settings.TELERIVET_API_KEY)
        project = tr.initProjectById(settings.TELERIVET_PROJECT_ID)

        telerivet_response = project.sendMessage(
            content=text,
            to_number=phonenumber
        )

        response = telerivet_response if isinstance(telerivet, dict) else json.loads(telerivet_response)
        return {
            "handler": Message.MessageProviders.Telerivet,
            "delivery_status": response["status"],
            "provider_id": response["id"],
            "cost": settings.TELERIVET_SMS_SEND_COST,
            "currency_code": settings.TELERIVET_SMS_SEND_CURRENCY,
        }


class Africastalking(TelecomHandler):
    @staticmethod
    def send_sms(self, phonenumber, text):
        africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        sms = africastalking.SMS
        response = sms.send(text, [phonenumber, ], )
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