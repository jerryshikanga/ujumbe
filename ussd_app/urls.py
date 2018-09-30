from . import views
from ussd.views import AfricasTalkingUssdGateway
from django.urls import path

urlpatterns = [
    path("at/", AfricasTalkingUssdGateway.as_view(), name="africastalking_ussd"),
]