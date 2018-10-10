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

    phonenumber = models.CharField(max_length=20, null=False, blank=False)
    text = models.TextField(null=False, blank=False)
    handler = models.CharField(null=False, blank=False, choices=MessageProviders.choices, max_length=100, default=MessageProviders.Africastalking)

    class Meta:
        abstract = True

    def __str__(self):
        return "SMS, Phone {} Through {} on {}. Text {}".format(self.phonenumber, self.handler, self.created.strftime("%Y-%m-%d %H:%M"), self.text)

    @property
    def summary(self):
        return "SMS : Phone {} on {}.".format(self.phonenumber, self.created.strftime("%Y-%m-%d %H:%M"))


class IncomingMessage(Message):
    """Will hold sent and received messages"""
    africastalking_id = models.CharField(max_length=255, null=False, blank=False)
    link_id = models.CharField(max_length=255, null=True, blank=True)
    shortcode = models.CharField(max_length=10, null=False, blank=False)


@with_author
class OutgoingMessages(Message):
    class MessageDeliveryStatus(DjangoChoices):
        Failed = ChoiceItem("failed")
        Sent = ChoiceItem("Sent")
        Delivered = ChoiceItem("Delivered")
        Unknown = ChoiceItem("Unknown")
    cost = models.CharField(null=False, blank=False, default="", max_length=10)
    delivery_status = models.CharField(null=False, blank=False, max_length=20, choices=MessageDeliveryStatus.choices,
                                       default="UNKNOWN")


@with_author
class UssdSession(TimeStampedModel):
    session_id = models.CharField(max_length=100, null=True, blank=True)
    phonenumber = models.CharField(max_length=34, null=True, blank=True)
    service_code = models.CharField(max_length=10, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
