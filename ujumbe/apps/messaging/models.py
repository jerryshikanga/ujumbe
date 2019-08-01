# Create your models here.
import logging

from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models, transaction
from django_extensions.db.models import TimeStampedModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from author.decorators import with_author
from djchoices import DjangoChoices, ChoiceItem
from phonenumber_field.validators import validate_international_phonenumber

from ujumbe.apps.profiles.models import Profile, Subscription, AccountCharges
from ujumbe.apps.weather.models import Location, CurrentWeather

logger = logging.getLogger(__name__)


class MessageException(Exception):
    pass


# Create your models here.
class Message(TimeStampedModel):
    class MessageProviders(DjangoChoices):
        Africastalking = ChoiceItem("Africastalking")
        Nexmo = ChoiceItem("Nexmo")
        Telerivet = ChoiceItem("Telerivet")

    phonenumber = PhoneNumberField(null=False, blank=False)
    processed = models.BooleanField(default=False)
    text = models.TextField(null=False, blank=False)
    handler = models.CharField(null=False, blank=False, choices=MessageProviders.choices, max_length=100)
    provider_id = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        abstract = True

    def __str__(self):
        return "SMS, Phone {} Through {} on {}. Text {}".format(self.phonenumber, self.handler,
                                                                self.created.strftime("%Y-%m-%d %H:%M"), self.text)

    @property
    def summary(self):
        return "SMS : Phone {} on {}.".format(self.phonenumber, self.created.strftime("%Y-%m-%d %H:%M"))

    def get_formatted_message_keywords(self):
        keywords = ""
        for key in MessageKeywords.choices:
            keywords += key[1] + " "
        return keywords

    def mark_processed(self):
        self.processed = True
        self.save()


class IncomingMessage(Message):
    datetime_sent = models.DateTimeField(blank=True, null=True)
    shortcode = models.CharField(max_length=20, null=False, blank=False)

    def check_shortcode_phonenumer_match(self):
        # number sending to itself so skip
        return self.shortcode == self.phonenumber

    def is_keyword_valid(self):
        parts = self.text.split("*") if "*" in self.text else self.text.split(" ")
        keyword = str(parts[0]).lower().strip()
        choices = [str(MessageKeywords.choices[index][0]).lower().strip() for index, value in
                   enumerate(MessageKeywords.choices)]
        return keyword in choices

    def is_profile_registered(self):
        return Profile.objects.filter(telephone=self.phonenumber).exists()

    def process(self):
        with transaction.atomic():
            self.process_response()

    def process_response(self):
        parts = self.text.split("*") if "*" in self.text else self.text.split(" ")
        keyword = str(parts[0]).upper().strip()

        # Check if sender is same as recipient and skip
        if not self.check_shortcode_phonenumer_match():
            self.mark_processed()
            return

        # Check if the keyword is valid, if not raise
        if not self.is_keyword_valid():
            response = "Your keyword {} is invalid. Try again with either {}. ".format(
                keyword, self.get_formatted_message_keywords())
            OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=response)
            self.mark_processed()
            return

        # Check if the user is registered
        if keyword != MessageKeywords.Register and not self.is_profile_registered():
            text = "Please register for Ujumbe to use any of its services"
            OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=text)
            return

        if keyword == MessageKeywords.Register:
            if len(parts) < 3:
                self.mark_processed()
                OutgoingMessages.objects.create(text="Please provide both first and last name",
                                                phonenumber=self.phonenumber)
                return
            from ujumbe.apps.profiles.tasks import create_profile
            create_profile(first_name=parts[1], last_name=parts[2], phonenumber=str(self.phonenumber))
        elif keyword == MessageKeywords.CurrentWeather:
            from ujumbe.apps.weather.tasks import process_current_weather_request
            detailed = False
            location_name = None
            if len(parts) > 1:
                if parts[1] == "DETAILED":
                    detailed = True
                if parts[1] == "SUMMARY":
                    detailed = False
                else:
                    location_name = parts[1]
            if len(parts) > 2:
                location_name = parts[2]
            process_current_weather_request(self.phonenumber, detailed, location_name)
        elif keyword == MessageKeywords.Location:
            if len(parts) <= 1:
                response = "Please provide a location name."
                OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=response)
            else:
                location_name = parts[1]
                from ujumbe.apps.profiles.tasks import set_user_location
                set_user_location(location_name, self.phonenumber)
        elif keyword == MessageKeywords.Language:
            if len(parts) < 2:
                response = "Please provide a language. Currently available choices are en, sw."
                OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=response)
                self.mark_processed()
                return
            from ujumbe.apps.profiles.tasks import set_user_language
            set_user_language(self.phonenumber, parts[1])
        elif keyword == MessageKeywords.Subscribe:
            subscription_type = parts[1]
            frequency = parts[2]
            location_name = parts[3] if len(parts) > 3 else None
            from ujumbe.apps.profiles.tasks import create_subscription
            create_subscription(self.phonenumber, subscription_type, frequency, location_name)
        elif keyword == MessageKeywords.Unsubscribe:
            from ujumbe.apps.profiles.tasks import cancel_user_subscriptions
            cancel_user_subscriptions(self.phonenumber)
        elif keyword == MessageKeywords.Forecast:
            response = "This feature is coming soon! Stay put. "
            OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=response)
        elif keyword == MessageKeywords.Market:
            from ujumbe.apps.marketdata.tasks import send_user_product_price_today
            if len(parts) > 1:
                product_name = parts[1]
                location_name = None
                if len(parts) > 2:
                    location_name = parts[2]
                send_user_product_price_today.delay\
                    (product_name, phonenumber=str(self.phonenumber), location_name=location_name)
            else:
                response = "Please provide product name."
                OutgoingMessages.objects.create(phonenumber=self.phonenumber, text=response)

        self.mark_processed()


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
    translated_text = models.TextField()

    def process(self):
        with transaction.atomic():
            self.send()

    def send(self):
        profile = None
        profile_qs = Profile.objects.filter(telephone=self.phonenumber)
        if profile_qs.exists():
            profile = profile_qs.first()
        validate_international_phonenumber(self.phonenumber)

        text = self.text
        if profile is not None and profile.language_code != Profile.SupportedLanguages.English:
            from .tasks import translate_text
            self.translated_text = translate_text("en", profile.language_code, text=self.text)
            self.save()
            text = self.translated_text

        data = None
        if settings.TELERIVET_PROJECT_ID and settings.TELERIVET_API_KEY:
            self.handler = Message.MessageProviders.Telerivet
            from .handlers import Telerivet
            data = Telerivet.send_sms(phonenumber=str(self.phonenumber), text=text)
        else:
            self.handler = Message.MessageProviders.Africastalking
            from .handlers import Africastalking
            data = Africastalking.send_sms(phonenumber=str(self.phonenumber), text=text)

        charge = AccountCharges.objects.create(
            profile=profile,
            cost=float(data["cost"]),
            currency_code=data["currency_code"],
            description="SMS {}".format(self.id)
        )
        self.charge = charge
        self.provider_id = data["provider_id"]
        self.handler = data["handler"]
        self.delivery_status = data["delivery_status"]
        self.save()
        self.mark_processed()


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

    def update_last_response(self, response=None):
        if response is not None:
            self.last_response = response
            self.save()
        return


class MessageKeywords(DjangoChoices):
    Register = ChoiceItem("REGISTER")
    CurrentWeather = ChoiceItem("WEATHER")
    Subscribe = ChoiceItem("SUBSCRIBE")
    Unsubscribe = ChoiceItem("UNSUBSCRIBE")
    Location = ChoiceItem("LOCATION")
    Forecast = ChoiceItem("FORECAST")
    Language = ChoiceItem("LANGUAGE")
    Market = ChoiceItem("MARKET")
