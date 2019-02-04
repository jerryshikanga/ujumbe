# Create your models here.
import logging

from phonenumber_field.modelfields import PhoneNumberField
from django.db import models, transaction
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author
from djchoices import DjangoChoices, ChoiceItem


from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.weather.models import Location, CurrentWeather

logger = logging.getLogger(__name__)


# Create your models here.
class Message(TimeStampedModel):
    class MessageProviders(DjangoChoices):
        Africastalking = ChoiceItem("Africastalking")
        Nexmo = ChoiceItem("Nexmo")
        Telerivet = ChoiceItem("Telerivet")

    phonenumber = PhoneNumberField(null=False, blank=False)
    text = models.TextField(null=False, blank=False)
    handler = models.CharField(null=False, blank=False, choices=MessageProviders.choices, max_length=100)
    provider_id = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        abstract = True

    def __str__(self):
        return "SMS, Phone {} Through {} on {}. Text {}".format(self.phonenumber, self.handler, self.created.strftime("%Y-%m-%d %H:%M"), self.text)

    @property
    def summary(self):
        return "SMS : Phone {} on {}.".format(self.phonenumber, self.created.strftime("%Y-%m-%d %H:%M"))


class IncomingMessage(Message):
    datetime_sent = models.DateTimeField(blank=True, null=True)
    shortcode = models.CharField(max_length=20, null=False, blank=False)
    processed = models.BooleanField(default=False)
    response = models.TextField(blank=True, null=True, default="")

    @classmethod
    def process_pending_messages(cls):
        with transaction.atomic():
            messages = IncomingMessage.objects.select_for_update().filter(processed=False)
            responses = []
            for message in messages:
                # number sending to itself so skip
                shortcode = str(message.shortcode) if str(message.shortcode).startswith("+") else "+{}".format(
                    message.shortcode)
                if shortcode == message.phonenumber:
                    logger.warning(
                        "Short-code match phone number {} for message {}.".format(message.shortcode, message))
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
                                response = Profile.create_customer_account(
                                    first_name=first_name, last_name=last_name,
                                    phonenumber=str(message.phonenumber)
                                )
                            else:
                                # no account, no operation allowed
                                response = "Please create an account by sending REGISTER*{first_name}*{last_name}."
                        else:
                            profile = Profile.objects.get(telephone=message.phonenumber)
                            if keyword == str(MessageKeywords.Register).lower().strip():
                                response = "You are already registered."
                            elif keyword == str(MessageKeywords.Weather).lower().strip():
                                detailed = True if len(parts) > 1 and parts[1].upper() == "DETAILED" else False
                                if len(parts) >= 2:
                                    # location name provided, use that
                                    location = Location.try_resolve_location_by_name(name=parts[2],
                                                                                     phonenumber=str(
                                                                                         message.phonenumber))
                                    if location is None:
                                        response = "Location named {} could not be determined. Please contact support.". \
                                            format(parts[2])
                                    else:
                                        response = CurrentWeather.get_current_location_weather_text(
                                            location_id=location.id, detailed=detailed)
                                        if profile.location is None:
                                            profile.location = location
                                            profile.save()
                                            response += "Your default location has been set to {}".format(location.name)
                                elif profile.location is not None:
                                    response = CurrentWeather.get_current_location_weather_text(
                                        location_id=profile.location_id, detailed=detailed)
                                else:
                                    response = "Please set profile default location or provide location name."

                            elif keyword == str(MessageKeywords.Location).lower().strip():
                                if len(parts) <= 1:
                                    response = "Please provide a location name."
                                else:
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
                    if response is not None and str(response).strip() != "":
                        message.response = response
                        responses.append({
                            "phonenumber": str(message.phonenumber),
                            "text": response
                        })
                message.processed = True
                message.save()
            return responses


@with_author
class OutgoingMessages(Message):
    class MessageDeliveryStatus(DjangoChoices):
        failed = ChoiceItem("Failed")
        sent = ChoiceItem("Sent")
        Delivered = ChoiceItem("Delivered")
        submitted = ChoiceItem("Submitted")
        buffered = ChoiceItem("Buffered")
        rejected = ChoiceItem("Rejected")
        success = ChoiceItem("Success")
    charge = models.ForeignKey("profiles.AccountCharges", null=True, blank=True, on_delete=models.SET_NULL)
    delivery_status = models.CharField(null=False, blank=False, max_length=50, choices=MessageDeliveryStatus.choices,
                                       default=MessageDeliveryStatus.submitted)
    failure_reason = models.CharField(null=True, blank=True, max_length=50)


@with_author
class UssdSession(TimeStampedModel):
    session_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    phonenumber = models.CharField(max_length=34, null=True, blank=True)
    service_code = models.CharField(max_length=10, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    last_response = models.TextField(null=True, blank=True)

    class Meta(object):
        verbose_name_plural = "Ussd Sessions"
        verbose_name = "Ussd Session"
        ordering = ["modified", ]

    def __str__(self):
        return "{} {} {}".format(self.phonenumber, self.modified, self.text)

    def update_last_response(self, response = None):
        if response is not None:
            self.last_response = response
            self.save()
        return


class MessageKeywords(DjangoChoices):
    Register = ChoiceItem("REGISTER")
    Weather = ChoiceItem("WEATHER")
    Subscribe = ChoiceItem("SUBSCRIBE")
    Unsubscribe = ChoiceItem("UNSUBSCRIBE")
    Location = ChoiceItem("LOCATION")
    Forecast = ChoiceItem("FORECAST")