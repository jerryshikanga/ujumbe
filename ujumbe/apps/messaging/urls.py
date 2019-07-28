from django.urls import path
from ujumbe.apps.messaging import views

app_name = "messaging"

urlpatterns = [
    path("telerivet/callback/", views.TelerivetWebhookView.as_view(), name="telerivet_webhook_view"),
    path("sms/incoming/", views.ATIncomingMessageCallbackView.as_view(), name="incoming_message_callback"),
    path("sms/outgoing/", views.AtOutgoingSMSCallback.as_view(), name="outgoing_message_callback"),
    path("ussd/callback/", views.AtUssdcallbackView.as_view(), name="at_ussd_callback_view"),
]
