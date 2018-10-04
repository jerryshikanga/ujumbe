from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author
from ujumbe.apps.weather.models import Location

# Create your models here.
User = get_user_model()


# Create your models here.
@with_author
class Profile(TimeStampedModel):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    telephone = models.CharField(max_length=15, null=False, blank=False, verbose_name="Telephone Number", unique=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    balance = models.IntegerField(default=0, null=False, blank=False)

    @property
    def full_name(self):
        return self.user.get_full_name()

    def __str__(self):
        return "Name : {} Phone : {}.".format(self.full_name, self.telephone)

    class Meta:
        unique_together = ("user", "telephone")
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


@with_author
class AccountCharges(TimeStampedModel):
    cost = models.IntegerField(null=False, blank=False)
    profile = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return "Charge of {} to {} for {}.".format(self.cost, self.profile.full_name, self.description)

    class Meta:
        verbose_name_plural = "Charges"
        verbose_name = "Charge"


class SubscriptionManager(models.Manager):
    def active(self):
        return super(SubscriptionManager, self).get_queryset().filter(active=True)

    def inactive(self):
        return super(SubscriptionManager, self).get_queryset().filter(active=False)


@with_author
class Subscription(TimeStampedModel):
    SubscriptionTypes = [
        ("CURRENT", "CURRENT"),
        ("FORECAST", "FORECAST"),
    ]

    subscription_type = models.CharField(choices=SubscriptionTypes, default="FORECAST", null=False, blank=False,
                                         max_length=50)
    profile = models.ForeignKey(Profile, null=False, blank=False, on_delete=models.CASCADE)
    frequency = models.TimeField(null=False, blank=False)
    last_send = models.DateTimeField(null=False, blank=False, default=timezone.now)
    active = models.BooleanField(default=True, null=False, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)

    objects = SubscriptionManager()

    def __str__(self):
        return "User {} subscription for {} of frequency {}".format(self.profile.full_name, self.subscription_type,
                                                                    self.frequency)

    @property
    def sms_description(self):
        return "Subscription to {} frequency {}".format(self.profile.full_name, self.frequency)

    def deactivate(self):
        self.active = False
        self.save()

    def activate(self):
        self.active = True
        self.save()
