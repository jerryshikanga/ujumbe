from celery import task

from ujumbe.apps.africastalking.models import IncomingMessage, MessageKeywords
from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.profiles.tasks import update_profile_location, send_sms
from ujumbe.apps.weather.models import CurrentWeather


@task
def process_incoming_messages(self):
    unprocessed_incoming_messages = IncomingMessage.objects.filter(processed=False)

    for message in unprocessed_incoming_messages:
        parts = message.text.split("*")
        keyword = parts[0]
        profile = Profile.objects.filter(telephone=message.phonenumber).first()
        response = ""
        if keyword == MessageKeywords.Register:
            response += "You are already registered. "
        elif keyword == MessageKeywords.Weather:
            summary = False if parts[1].upper() == "DETAILED" else True
            weather = CurrentWeather.objects.filter(
                location=profile.location
            ).order_by("-created").first()
            response += weather.summary if summary else weather.detailed
        elif keyword == MessageKeywords.Location:
            location_str = parts[1]
            update_profile_location.delay(phonenumber=message.phonenumber, location_str=location_str)
            response += "Your request has been received successfully. "
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
                response += subscription.sms_description
            else:
                response += "You already have a similar subscription. "
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
            response += "You have deactivated {} subscriptions. ".format(subscriptions.count())
        elif keyword == MessageKeywords.Forecast:
            response += "This feature is coming soon! Stay put. "
        else:
            keywords = ""
            for key in MessageKeywords.choices:
                keywords += key[1] + " "
            response += "Your entry {} is invalid. Try again with either {}. ".format(message.text, keywords)
        send_sms.delay(phonenumber=message.phonenumber, text=response)
        message.processed = True
        message.save()