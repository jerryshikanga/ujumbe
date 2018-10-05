from django.contrib import admin
from ujumbe.apps.africastalking.models import IncomingMessage, OutgoingMessages

# Register your models here.
admin.site.register(IncomingMessage)
admin.site.register(OutgoingMessages)
