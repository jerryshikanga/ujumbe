from django.db import models
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author


# Create your models here.
@with_author
class Message(TimeStampedModel):
    """Will hold sent and received messages"""
    from_telephone = models.CharField(max_length=20, null=False, blank=False)
    to_telephone = models.CharField(max_length=20, null=False, blank=False)
    text = models.CharField(max_length=255, null=False, blank=False)
    africastalking_id = models.CharField(max_length=255, null=False, blank=False)
    link_id = models.CharField(max_length=255, null=True, blank=True)
