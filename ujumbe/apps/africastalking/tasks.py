from celery import task
from django.db import transaction

from ujumbe.apps.africastalking.models import IncomingMessage, MessageKeywords
from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.profiles.tasks import update_profile_location, send_sms, create_customer_account
from ujumbe.apps.weather.models import CurrentWeather


@task
def process_incoming_messages():
    with transaction.atomic():
        unprocessed_incoming_messages = IncomingMessage.objects.select_for_update().filter(processed=False)  # added
        # select for update to for atomic processing to prevent double processing of ,essages

        for message in unprocessed_incoming_messages:
            # number sending to itself so skip
            if message.shortcode == message.phonenumber:
                pass
            else:
                parts = message.text.split("*")
                keyword = str(parts[0]).lower()
                choices = [str(MessageKeywords.choices[index][0]).lower() for index, value in
                           enumerate(MessageKeywords.choices)]
                if keyword not in choices:
                    # notify use that his choice is wrong
                    keywords = ""
                    for key in MessageKeywords.choices:
                        keywords += key[1] + " "
                    response = "Your entry {} is invalid. Try again with either {}. ".format(message.text, keywords)
                else:
                    if not Profile.objects.filter(telephone=message.phonenumber).exists():
                        if keyword == MessageKeywords.Register:
                            first_name = parts[1]
                            last_name = parts[2]
                            create_customer_account.delay(first_name=first_name, last_name=last_name,
                                                          phonenumber=message.phonenumber)
                            response = "Your account will be created shortly. You will be notified via sms."
                        else:
                            # no account, no operation allowed
                            response = "Please create an account by sending REGISTER {first_name} {last_name}."
                    else:
                        profile = Profile.objects.get(telephone=message.phonenumber)
                        if keyword == MessageKeywords.Register:
                            response = "You are already registered. "
                        elif keyword == MessageKeywords.Weather:
                            summary = False if parts[1].upper() == "DETAILED" else True
                            weather = CurrentWeather.objects.filter(
                                location=profile.location
                            ).order_by("-created").first()
                            response = weather.summary if summary else weather.detailed
                        elif keyword == MessageKeywords.Location:
                            location_str = parts[1]
                            update_profile_location.delay(phonenumber=message.phonenumber, location_str=location_str)
                            response = "Your request has been received successfully. "
                        elif keyword == MessageKeywords.Subscribe:
                            subscription_type = parts[1]
                            frequency = parts[2]
                            location = parts[3] if parts[3] is not None else profile.location
                            subscription, created = Subscription.objects.get_or_create(
                                profile=profile,
                                subscription_type=subscription_type,
                                frequency=frequency,
                                location=location
                            )
                            if created:
                                response = subscription.sms_description
                            else:
                                response = "You already have a similar subscription. "
                        elif keyword == MessageKeywords.Unsubscribe:
                            subscriptions = Subscription.objects.filter(
                                profile=profile
                            )
                            subscription_type = parts[1] if parts[1] is not None else None
                            if subscription_type: subscriptions.filter(subscription_type__iexact=subscription_type)

                            frequency = parts[2] if parts[2] is not None else None
                            if frequency: subscriptions.filter(frequency=frequency)

                            location = parts[3] if parts[3] is not None else None
                            if location: subscriptions.filter(location=location)

                            [subscription.deactivate() for subscription in subscriptions]
                            response = "You have deactivated {} subscriptions. ".format(subscriptions.count())
                        elif keyword == MessageKeywords.Forecast:
                            response = "This feature is coming soon! Stay put. "
                        else:
                            response = "Your entry {} is invalid.".format(message.text)
                send_sms.delay(phonenumber=str(message.phonenumber), text=response)
            message.processed = True
            message.save()
