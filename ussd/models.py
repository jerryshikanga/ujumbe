from django.db import models
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author


# Create your models here.
@with_author
class UssdSession(TimeStampedModel):
    session_id = models.CharField(max_length=20, null=False, blank=False)
    phone_number = models.CharField(max_length=20, null=False, blank=False)
    current_step = models.CharField(max_length=20, null=True, blank=True)
