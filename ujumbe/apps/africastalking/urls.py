from django.urls import path
from ujumbe.apps.africastalking import views

app_name = "africastalking"

urlpatterns = [
    path("sms/callback/", views.ATMessageCallbackView.as_view(), name="at_message_callback_view"),
]
