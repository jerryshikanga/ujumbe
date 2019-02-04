import logging

from celery import task
from django.conf import settings
from django.contrib.auth import get_user_model
from phonenumber_field.validators import validate_international_phonenumber

from ujumbe.apps.africastalking.models import OutgoingMessages
from ujumbe.apps.profiles.models import Profile, AccountCharges, Subscription
from ujumbe.apps.weather.models import Location
from ujumbe.apps.weather.utils import ForecastPeriods
from ujumbe.apps.profiles.handlers import Telerivet, Africastalking

User = get_user_model()

logger = logging.getLogger(__name__)


@task
def send_sms(phonenumber: str, text: str):
    validate_international_phonenumber(phonenumber)
    data = Telerivet.send_sms(phonenumber=phonenumber, text=text) \
        if settings.TELERIVET_PROJECT_ID and settings.TELERIVET_API_KEY \
        else Africastalking.send_sms(phonenumber=phonenumber, text=text)

    profile = Profile.objects.get(telephone=phonenumber) if Profile.objects.filter(
        telephone=phonenumber).exists() else None
    charge = AccountCharges.objects.create(
        profile=profile,
        cost=float(data["cost"]),
        currency_code=data["currency_code"],
    )
    outgoing_sms = OutgoingMessages.objects.create(
        phonenumber=phonenumber,
        text=text,
        handler=data["handler"],
        delivery_status=data["delivery_status"],
        provider_id=data["provider_id"],
        charge=charge
    )
    charge.description = outgoing_sms.summary
    charge.save()
    return outgoing_sms


@task
def create_user_forecast_subscription(phonenumber: str, location_id: int, frequency: int):
    frequency = ForecastPeriods[frequency]
    p = Profile.objects.filter(telephone=phonenumber).first()
    s = Subscription.objects.create(
        location_id=location_id,
        profile=p,
        subscription_type=Subscription.SubscriptionTypes.forecast,
        frequency=frequency
    )
    text = "Subscription {} created successfully.".format(str(s))
    send_sms.delay(phonenumber=phonenumber, text=text)


@task
def end_user_subscription(phonumber: str, subscription_id: int):
    s = Subscription.objects.get(id=subscription_id)
    s.deactivate()
    send_sms.delay(phonenumber=phonumber, text="Deactivated subscription {}".format(s))


@task
def send_user_balance_notification(phonenumber: str):
    p = Profile.objects.filter(telephone=phonenumber).first()
    text = "Account {} Balance {}".format(p.full_name, p.balance)
    send_sms.delay(phonenumber=phonenumber, text=text)


@task
def send_user_account_charges(phonenumber: str):
    p = Profile.objects.filter(telephone=phonenumber).first()
    charges = AccountCharges.objects.filter(profile=p)
    text = ""
    for c in charges:
        text += str(c)
    send_sms.delay(phonenumber=phonenumber, text=text)


@task
def set_user_location(location_id: int, phonenumber: str):
    p = Profile.objects.filter(telephone=phonenumber).first()
    l = Location.objects.get(id=location_id)
    text = ""
    init_loc_text = "Your location has been changed from {}".format(str(p.location)) if p.location else None
    p.location = l
    p.save()
    if init_loc_text is not None:
        text += "to {} ".format(str(l))
    else:
        text = "Your location has been set to {}.".format(str(l))
    send_sms.delay(phonenumber=phonenumber, text=text)


@task
def check_and_send_user_subscriptions():
    subscriptions = Subscription.objects.due()
    for subscription in subscriptions:
        try:
            send_sms.delay(text=subscription.sms_description, phonenumber=str(subscription.profile.telephone))
        except Exception as e:
            logging.error("Error sending subscription"+str(e))
    logging.info("Sent {} subscriptions".format(len(subscriptions)))
