from django.contrib import admin
from ujumbe.apps.profiles.models import AccountCharges, Profile, Subscription

# Register your models here.
admin.site.register(AccountCharges)
admin.site.register(Profile)
admin.site.register(Subscription)
