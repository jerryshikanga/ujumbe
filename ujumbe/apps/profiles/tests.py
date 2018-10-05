from django.test import TestCase
import africastalking, json
from ujumbe.apps.profiles.tasks import send_sms


# Create your tests here.
class SMSTests(TestCase):
    def test_somtel_message_delivery(self):
        # disclaimer : this will send an actual message
        send_sms.delay(phonenumber=int("+252621113022"), text="Hello there, Jerry sent this")
