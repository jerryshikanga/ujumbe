import datetime
import logging

from author.decorators import with_author
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField
from djchoices import DjangoChoices, ChoiceItem

from ujumbe.apps.weather.models import Location

# Create your models here.
User = get_user_model()
logger = logging.getLogger(__name__)


# Create your models here.
@with_author
class Profile(TimeStampedModel):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    telephone = PhoneNumberField(unique=True, null=False, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    balance = models.FloatField(default=0, null=False, blank=False)

    def __str__(self):
        return "Name : {} Phone : {}.".format(self.user.get_full_name() if self.user.get_full_name() is not None
                                              else self.user.username, self.telephone)

    class Meta:
        unique_together = ("user", "telephone")
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    @classmethod
    def create_customer_account(cls, first_name: str, last_name: str, phonenumber: str, password: str = None,
                                email: str = None):
        if Profile.objects.filter(telephone=phonenumber).exists():
            message = "Cant create profile with phone number {}. It already exists".format(phonenumber)
        else:
            username = email if email is not None else str(first_name + last_name).strip().replace(" ", "").lower()
            if User.objects.filter(username=username).exists():
                import random, datetime
                random.seed(datetime.datetime.now())
                username = str(random.randint(1, 99)) + username
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            if email is not None:
                user.email = email
            password = password if password is not None else phonenumber
            user.set_password(password)
            user.save()
            profile = Profile.objects.create(
                user=user,
                telephone=phonenumber
            )
            message = "Hello {}, your account has been created successfully. Your username is {}".format(
                profile.user.get_full_name(), profile.user.username)
        return message


@with_author
class AccountCharges(TimeStampedModel):

    cost = models.FloatField(null=False, blank=False)
    currency_code = models.CharField(null=False, blank=False, default="KES", max_length=5)
    profile = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return "Charge of {} to {} for {}.".format(self.cost, self.profile, self.description)

    class Meta:
        verbose_name_plural = "Charges"
        verbose_name = "Charge"


@receiver(post_save, sender=AccountCharges)
def update_balance_on_charge(sender, instance, created, **kwargs):
    if created and instance.profile is not None:
        instance.profile.balance -= float(instance.cost)
        instance.profile.save()


class SubscriptionManager(models.Manager):
    def for_phonenumber(self, phonenumber: str):
        profile = Profile.objects.filter(telephone=phonenumber).first()
        return super(SubscriptionManager, self).get_queryset().filter(profile=profile)

    def due(self):
        time_now = datetime.datetime.now()
        return Subscription.objects.filter(last_send__lte=time_now-F("frequency")).filter(active=True)

    def active(self):
        return super(SubscriptionManager, self).get_queryset().filter(active=True)

    def inactive(self):
        return super(SubscriptionManager, self).get_queryset().filter(active=False)


@with_author
class Subscription(TimeStampedModel):
    class SubscriptionTypes(DjangoChoices):
        forecast = ChoiceItem("FORECAST")
        current = ChoiceItem("CURRENT")

    subscription_type = models.CharField(choices=SubscriptionTypes.choices, default=SubscriptionTypes.forecast,
                                         null=False, blank=False,
                                         max_length=50)
    profile = models.ForeignKey(Profile, null=False, blank=False, on_delete=models.CASCADE)
    frequency = models.DurationField(null=False, blank=False)
    last_send = models.DateTimeField(null=False, blank=False, default=timezone.now)
    active = models.BooleanField(default=True, null=False, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)

    objects = SubscriptionManager()

    def __str__(self):
        return "Subscription for {} of frequency {}".format(self.subscription_type, self.frequency)

    @property
    def sms_description(self):
        return "Subscription to {} frequency {}".format(self.profile, self.frequency)

    def deactivate(self):
        self.active = False
        self.save()

    def activate(self):
        self.active = True
        self.save()
