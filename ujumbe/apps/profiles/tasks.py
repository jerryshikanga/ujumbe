from django.contrib.auth import get_user_model
from django.conf import settings
from ujumbe.apps.weather.models import Location
from ujumbe.apps.profiles.models import Profile, AccountCharges
from ujumbe.apps.africastalking.models import OutgoingMessages
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
    response = "Hello {}, your account has been created successfully. Your username is {}".format(profile.full_name, profile.user.username)
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
            response = "location {} could not be determined. Kindly try again with your county name.".format(profile.location.name)
        send_sms.delay(phonenumber=profile.telephone, text=response)
        return location_exists
    else:
        logging.warning("Profile with phone {} not found. Can't update location.".format(phonenumber))
        return False

@task
def send_sms(phonenumber: int, text: str):
    africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
    sms = africastalking.SMS
    # disabled to save on costs
    # response = sms.send(text, [phonenumber, ])
    # status_code = int(response["SMSMessageData"]["Recipients"][0]["statusCode"])
    # cost = str(response["SMSMessageData"]["Recipients"][0]["cost"])

    cost = 0
    status_code = 101

    from ujumbe.apps.africastalking.models import Message
    outgoing_sms = OutgoingMessages.objects.create(
        phonenumber=phonenumber,
        cost=cost,
        text=text,
        handler=Message.MessageProviders.Africastalking
    )

    if status_code == 0:
        profile = Profile.objects.get(telephone=phonenumber) if Profile.objects.filter(
            telephone=phonenumber).exists() else None
        if profile is not None:
            profile.balance -= cost
            profile.save()
        AccountCharges.objects.create(
            profile=profile,
            cost=cost,
            description=outgoing_sms.summary
        )

        outgoing_sms.delivery_status = OutgoingMessages.MessageDeliveryStatus.Sent
        outgoing_sms.save()
        return True
    else:
        logging.warning("Failed to send message {}".format(str(outgoing_sms)))
        return False
