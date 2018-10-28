from django.urls import path
from ujumbe.apps.africastalking import views

app_name = "africastalking"

urlpatterns = [
    path("sms/incoming/", views.ATIncomingMessageCallbackView.as_view(), name="incoming_message_callback"),
    path("sms/outgoing/", views.AtOutgoingSMSCallback.as_view(), name="outgoing_message_callback"),
    path("ussd/callback/", views.AtUssdcallbackView.as_view(), name="at_ussd_callback_view"),
]
