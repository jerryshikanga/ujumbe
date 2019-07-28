import logging

from celery import task
from django.contrib.auth import get_user_model

from ujumbe.apps.messaging.models import OutgoingMessages
from ujumbe.apps.profiles.models import Profile, AccountCharges, Subscription
from ujumbe.apps.weather.models import Location
from ujumbe.apps.weather.utils import ForecastPeriods

User = get_user_model()

logger = logging.getLogger(__name__)


@task
def create_profile(first_name, last_name, phonenumber, password=None, email=None):
    if Profile.objects.filter(telephone=phonenumber).exists():
        message = "An account with the phone number {} already exists".format(phonenumber)
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=message)
    else:
        username = str(phonenumber).replace("+", "")
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        if email is not None:
            user.email = email
        password = password if password is not None else phonenumber
        user.set_password(password)
        user.save()
        profile = Profile.objects.create(
            user=user,
            telephone=phonenumber
        )
        message = "Hello {}, your account has been created successfully. Your username is {}".format(
            profile.user.get_full_name(), profile.user.username)
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=message)


@task
def create_subscription(phonenumber, type, frequency, location_name):
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    location = profile.location
    if location_name is not None:
        resolved_location = Location.try_resolve_location_by_name(location_name)
        if resolved_location is None:
            text = "Location {} cannot be resolved.".format(location_name)
            OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)
            return
        location = resolved_location
    if location is None:
        text = "Please set a default location or provide location name."
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)
        return
    subscription, created = Subscription.objects.get_or_create(
        profile=profile,
        subscription_type=type,
        frequency=frequency,
        location=location
    )
    if created:
        response = subscription.sms_description
    else:
        response = "You already have a subscription {}. ".format(subscription)
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=response)


@task
def cancel_user_subscriptions(phonenumber):
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    # profile.subscription_set.


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
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)


@task
def end_user_subscription(phonumber: str, subscription_id: int):
    s = Subscription.objects.get(id=subscription_id)
    s.deactivate()
    text = "Deactivated subscription {}".format(s)
    OutgoingMessages.objects.create(phonenumber=phonumber, text=text)


@task
def send_user_balance_notification(phonenumber: str):
    p = Profile.objects.filter(telephone=phonenumber).first()
    text = "Account {} Balance {}".format(p.full_name, p.balance)
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)


@task
def send_user_account_charges(phonenumber: str):
    p = Profile.objects.filter(telephone=phonenumber).first()
    charges = AccountCharges.objects.filter(profile=p)
    text = ""
    for c in charges:
        text += str(c)
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)


@task
def set_user_location(location_name: str, phonenumber: str):
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    try:
        location = Location.try_resolve_location_by_name(name=location_name, phonenumber=phonenumber)
        if location is None:
            response = "Location named {} could not be determined. Please contact support.".format(location_name)
        else:
            profile.location = location
            profile.save()
            response = "Your location has been successfully set as {}".format(location.name)
    except Exception as e:
        logger.error(str(e))
        response = "Location named {} could not be determined. Please contact support.".format(location_name)
    finally:
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=response)


@task
def check_and_send_user_subscriptions():
    subscriptions = Subscription.objects.due()
    if subscriptions.count() > 0:
        for subscription in subscriptions:
            OutgoingMessages.objects.create(text=subscription.sms_description,
                                            phonenumber=str(subscription.profile.telephone))


@task
def set_user_language(phonenumber, language):
    if language not in ("en", "sw"):
        text = "Invalid language code. Currently available choices are en, sw."
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)
        return
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    profile.language_code = language
    profile.save()
    text = "Your language has been successfully set to {}".format(language)
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)
