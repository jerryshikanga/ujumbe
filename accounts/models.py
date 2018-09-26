from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth import get_user_model
from author.decorators import with_author

User = get_user_model()


# Create your models here.
@with_author
class Account(TimeStampedModel):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    telephone = models.CharField(max_length=15, null=False, blank=False, verbose_name="Telephone Number")
    