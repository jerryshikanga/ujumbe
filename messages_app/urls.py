from django.urls import path
from .views import AfricastalkingMessageCallback

urlpatterns = [
    path("callback/", AfricastalkingMessageCallback.as_view(), name="africatslaking_sms_callback_view"),
]
