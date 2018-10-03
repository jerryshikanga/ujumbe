from django.db import models
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author


# Create your models here.
@with_author
class IncomingMessage(TimeStampedModel):
    """Will hold sent and received messages"""
    phonenumber = models.CharField(max_length=20, null=False, blank=False)
    text = models.CharField(max_length=255, null=False, blank=False)
    africastalking_id = models.CharField(max_length=255, null=False, blank=False)
    link_id = models.CharField(max_length=255, null=True, blank=True)
    shortcode = models.CharField(max_length=10, null=False, blank=False)


@with_author
class OutgoingMessages(TimeStampedModel):
    MessageProviders = [
        ("AT", "Africastalking"),
        ("NEXMO", "Nexmo")
    ]
    MessageDeliveryStatus = [
        ("FAILED", "Failed"),
        ("SENT", "Sent"),
        ("DELIVERED", "Delivered"),
        ("UNKNOWN", "Unknown"),
    ]
    phonenumber = models.CharField(max_length=20, null=False, blank=False)
    text = models.TextField(null=True, blank=True)
    handler = models.CharField(null=False, blank=False, choices=MessageProviders, max_length=100)
    cost = models.CharField(null=False, blank=False, default="", max_length=10)
    delivery_status = models.CharField(null=False, blank=False, max_length=20, choices=MessageDeliveryStatus, default="UNKNOWN")

    def __str__(self):
        return "SMS sent to {} using {} on {}. Text {}".format(self.phonenumber, self.handler, self.created, self.text)

    @property
    def summary(self):
        return "SMS to {} on {}".format(self.phonenumber, self.created)
