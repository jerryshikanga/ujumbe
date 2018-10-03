import json
import logging

import africastalking
from celery import task
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Profile, AccountCharges
from messages_app.models import OutgoingMessages

User = get_user_model()


@task
def create_customer_account(first_name: str, last_name: str, phonenumber: str, password: str = "", email: str = None):
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name
    )
    if email is not None:
        user.email = email
    user.set_password(password)
    user.save()
    profile = Profile.objects.create(
        user=user,
        telephone=phonenumber
    )
    response = "Account created successfully"
    send_sms.delay(phonenumber=profile.telephone, text=response)


@task
def send_sms(phonenumber: int, text: str):
    africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
    sms = africastalking.SMS
    response = sms.send(text, [phonenumber, ])
    response = json.loads(response.replace("'", '"'))
    status_code = int(response["SMSMessageData"]["Recipients"][0]["statusCode"])
    cost = str(response["SMSMessageData"]["Recipients"][0]["cost"])

    outgoing_sms = OutgoingMessages.objects.create(
        phonenumber=phonenumber,
        cost=cost,
        text=text,
        handler="AT"
    )

    if status_code == 101:
        profile = Profile.objects.get(telephone=phonenumber)
        AccountCharges.objects.create(
            profile=profile,
            cost=cost,
            description=outgoing_sms.summary
        )
        outgoing_sms.delivery_status = "SENT"
        outgoing_sms.save()
    else:
        logging.warning("Error sending sms Phone {} Text {}".format(phonenumber, text))

