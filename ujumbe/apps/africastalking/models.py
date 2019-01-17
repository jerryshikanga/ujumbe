# Create your models here.
from django.db import models
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author
from djchoices import DjangoChoices, ChoiceItem


# Create your models here.
class Message(TimeStampedModel):
    class MessageProviders(DjangoChoices):
        Africastalking = ChoiceItem("Africastalking")
        Nexmo = ChoiceItem("Nexmo")
        Telerevivet = ChoiceItem("Telerivet")

    phonenumber = models.CharField(max_length=20, null=False, blank=False)
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
    link_id = models.CharField(max_length=255, null=True, blank=True)
    shortcode = models.CharField(max_length=10, null=False, blank=False)
    processed = models.BooleanField(default=False)


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