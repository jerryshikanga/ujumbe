from django.dispatch import receiver
from django.db.models.signals import post_save
from ujumbe.apps.africastalking.models import Message
from ujumbe.apps.profiles.models import Profile


@receiver(signal=post_save, sender=Message)
def charge_user_for_sms(sender, instance, created, **kwargs):
    if created:
        if Profile.objects.filter(telephone=instance.phonenumber).exists():
            pass
