from django.contrib import admin
from ujumbe.apps.messaging.models import IncomingMessage, OutgoingMessages, UssdSession

# Register your models here.
admin.site.register(IncomingMessage)
admin.site.register(OutgoingMessages)
admin.site.register(UssdSession)
