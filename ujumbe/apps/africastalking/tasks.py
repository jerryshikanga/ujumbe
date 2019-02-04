import logging

from celery import task
from django.db import transaction

from ujumbe.apps.africastalking.models import IncomingMessage, MessageKeywords
from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.profiles.tasks import send_sms, create_customer_account
from ujumbe.apps.weather.models import CurrentWeather, Location

logger = logging.getLogger(__name__)


@task
def process_incoming_messages():
    with transaction.atomic():
        unprocessed_incoming_messages = IncomingMessage.objects.select_for_update().filter(processed=False)  # added
        # select for update to for atomic processing to prevent double processing of ,messages
        responses = []
        for message in unprocessed_incoming_messages:
            # number sending to itself so skip
            shortcode = str(message.shortcode) if str(message.shortcode).startswith("+") else "+{}".format(
                message.shortcode)
            if shortcode == message.phonenumber:
                logger.warning("Short-code match phone number {} for message {}.".format(message.shortcode, message))
            else:
                parts = message.text.split("*") if "*" in message.text else message.text.split(" ")
                keyword = str(parts[0]).lower().strip()
                choices = [str(MessageKeywords.choices[index][0]).lower().strip() for index, value in
                           enumerate(MessageKeywords.choices)]
                if keyword not in choices:
                    # notify use that his choice is wrong
                    keywords = ""
                    for key in MessageKeywords.choices:
                        keywords += key[1] + " "
                    response = "Your keyword {} is invalid. Try again with either {}. ".format(keyword, keywords)
                else:
                    if not Profile.objects.filter(telephone=message.phonenumber).exists():
                        if keyword == str(MessageKeywords.Register).lower().strip():
                            first_name = parts[1]
                            last_name = parts[2]
                            response = create_customer_account(first_name=first_name, last_name=last_name,
                                                               phonenumber=str(message.phonenumber))
                        else:
                            # no account, no operation allowed
                            response = "Please create an account by sending REGISTER*{first_name}*{last_name}."
                    else:
                        profile = Profile.objects.get(telephone=message.phonenumber)
                        if keyword == str(MessageKeywords.Register).lower().strip():
                            response = "You are already registered."
                        elif keyword == str(MessageKeywords.Weather).lower().strip():
                            detailed = True if parts[1].upper() == "DETAILED" else False
                            if profile.location is None and len(parts) <= 2:
                                response = "Please set profile default location or provide location name."
                            else:
                                if parts[2]:
                                    location = Location.try_resolve_location_by_name(name=parts[2],
                                                                                     phonenumber=str(message.phonenumber))
                                else:
                                    location = profile.location
                                logger.error("Location {}".format(location))
                                if location is None:
                                    response = "Location named {} could not be determined. Please contact support.".\
                                        format(parts[2])
                                else:
                                    response = CurrentWeather.get_current_location_weather_text(
                                        location_id=location.id, detailed=detailed)
                                if location is not None and profile.location is None:
                                    profile.location = location
                                    profile.save()
                                    response += "Your default location has been set to {}".format(location.name)
                        elif keyword == str(MessageKeywords.Location).lower().strip():
                            location_str = parts[1]
                            try:
                                location = Location.try_resolve_location_by_name(
                                    name=location_str, phonenumber=profile.telephone)
                                profile.location = location
                                profile.save()
                                response = "Your location has been successfully set as {}".format(location.name)
                            except Exception as e:
                                response = "Location named {} could not be determined. Please contact support.".format(
                                    location_str)
                        elif keyword == str(MessageKeywords.Subscribe).lower().strip():
                            subscription_type = parts[1]
                            frequency = parts[2]
                            if profile.location is None and len(parts) <= 4:
                                response = "Please set profile default location or provide location name."
                            else:
                                location = parts[3] if len(parts) >= 4 else profile.location
                                subscription, created = Subscription.objects.get_or_create(
                                    profile=profile,
                                    subscription_type=subscription_type,
                                    frequency=frequency,
                                    location=location
                                )
                                if created:
                                    response = subscription.sms_description
                                else:
                                    response = "You already have a subscription {}. ".format(subscription)
                        elif keyword == str(MessageKeywords.Unsubscribe).lower().strip():
                            subscriptions = Subscription.objects.filter(
                                profile=profile
                            )
                            subscription_type = parts[1] if parts[1] is not None else None
                            if subscription_type:
                                subscriptions.filter(subscription_type__iexact=subscription_type)
                            frequency = parts[2] if parts[2] is not None else None
                            if frequency:
                                subscriptions.filter(frequency=frequency)

                            location = parts[3] if parts[3] is not None else None
                            if location:
                                subscriptions.filter(location=location)
                            [subscription.deactivate() for subscription in subscriptions]
                            response = "You have deactivated {} subscriptions. ".format(subscriptions.count())
                        elif keyword == str(MessageKeywords.Forecast).lower().strip():
                            response = "This feature is coming soon! Stay put. "
                        else:
                            response = "Your entry {} is invalid.".format(message.text)
                if response is not None and response != "":
                    send_sms.delay(phonenumber=str(message.phonenumber), text=response)
                    responses.append(response)
            message.processed = True
            message.save()
        return responses
