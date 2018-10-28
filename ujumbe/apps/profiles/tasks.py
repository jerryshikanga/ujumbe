from django.contrib.auth import get_user_model
from django.conf import settings
from ujumbe.apps.weather.models import Location
from ujumbe.apps.profiles.models import Profile, AccountCharges, Subscription
from ujumbe.apps.africastalking.models import OutgoingMessages, Message
from ujumbe.apps.weather.utils import ForecastPeriods
import africastalking
import logging
from celery import task

User = get_user_model()


@task
def create_customer_account(first_name: str, last_name: str, phonenumber: str, password: str = None, email: str = None):
    if Profile.objects.filter(telephone=phonenumber).exists():
        message = "Cant create profile with telephone {}. It already exists".format(phonenumber)
        logging.warning(message)
        send_sms.delay(phonenumber=phonenumber, text=message)
        return False
    username = email if email is not None else str(first_name + last_name).strip().replace(" ", "").lower()
    if User.objects.filter(username=username).exists():
        import random, datetime
        random.seed(datetime.datetime.now())
        username = str(random.randint(1, 99)) + username
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        username=username
    )
    if email is not None:
        user.email = email
    if password is None:
        password = phonenumber
    user.set_password(password)
    user.save()
    profile = Profile.objects.create(
        user=user,
        telephone=phonenumber
    )
    response = "Hello {}, your account has been created successfully. Your username is {}".format(profile.full_name,
                                                                                                  profile.user.username)
    send_sms.delay(phonenumber=profile.telephone, text=response)
    return True


@task
def update_profile_location(phonenumber: str, location_name):
    if Profile.objects.filter(telephone=phonenumber).exists():
        profile = Profile.objects.get(telephone=phonenumber)
        location_exists = Location.objects.filter(name__iexact=location_name).exists()
        if location_exists:
            profile.location = Location.objects.get(name__iexact=location_name)
            profile.save()
            response = "Your location has been updated succesfully"
        else:
            response = "location {} could not be determined. Kindly try again with your county name.".format(
                profile.location.name)
        send_sms.delay(phonenumber=profile.telephone, text=response)
        return location_exists
    else:
        logging.warning("Profile with phone {} not found. Can't update location.".format(phonenumber))
        return False


@task
def send_sms(phonenumber: str, text: str):
    try:
        africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        sms = africastalking.SMS
        response = sms.send(text, [phonenumber, ], )
        message_data = response["SMSMessageData"]["Recipients"][0]# only one recipient
        status_code = message_data["statusCode"]
        cost_str = message_data["cost"]
        cost_str_parts = str(cost_str).split(" ")
        currency_code = cost_str_parts[0]
        cost = cost_str_parts[1]
        status = message_data["status"]
        africastalking_id = message_data["messageId"]

        profile = Profile.objects.get(telephone=phonenumber) if Profile.objects.filter(
            telephone=phonenumber).exists() else None
        charge = AccountCharges.objects.create(
            profile=profile,
            cost=cost,
            currency_code=currency_code,
        )
        outgoing_sms = OutgoingMessages.objects.create(
            phonenumber=phonenumber,
            text=text,
            handler=Message.MessageProviders.Africastalking,
            delivery_status=status,
            provider_id=africastalking_id,
            charge=charge
        )
        charge.description = outgoing_sms.summary
        charge.save()

        return outgoing_sms
    except Exception as e:
        message = "Failed to send message. Error {}".format(str(e))
        logging.warning(message)

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
    message = "Sending subscriptions"
    print(message)
    logging.info(message)
