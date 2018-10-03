from django.contrib import admin
from .models import OutgoingMessages, IncomingMessage

# Register your models here.
admin.site.register(OutgoingMessages)
admin.site.register(IncomingMessage)
