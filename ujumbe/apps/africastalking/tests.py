from django.test import TestCase
from ujumbe.apps.africastalking.models import IncomingMessage
from ujumbe.apps.profiles.models import Profile
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import json
import datetime
from django.urls import reverse
from django_dynamic_fixture import G

User = get_user_model()


# Create your tests here.
class AfricastalkingViewTests(TestCase):
    def setUp(self):
        self.phonenumber = "+254727447101"
        self.at_shortcode = 20880

    def test_register_view(self):
            text = "REGISTER JERRY SHIKANGA"
            at_id = get_random_string(10)
            linkId = get_random_string(15)
            time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
            url = reverse("africastalking:at_message_callback_view")
            post_data = {
                "from": self.phonenumber,
                "to": self.at_shortcode,
                "text": text,
                "date": time,
                "id": at_id,
                "linkId": linkId
            }
            post_data = json.dumps(post_data)
            self.client.post(url, data=post_data, content_type="application/json")
            self.assertTrue(IncomingMessage.objects.filter(africastalking_id=at_id).exists(), "Incoming msg obj not "
                                                                                              "created")
            self.assertTrue(Profile.objects.filter(telephone=self.phonenumber).exists(), "Profile obj not created")

    def test_wrong_keyword(self):
        user  = G(User)
        Profile.objects.create(user=user, telephone=self.phonenumber)
        text = "TEST JERRY SHIKANGA"
        at_id = get_random_string(10)
        linkId = get_random_string(15)
        time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        url = reverse("africastalking:at_message_callback_view")
        post_data = {
            "from": self.phonenumber,
            "to": self.at_shortcode,
            "text": text,
            "date": time,
            "id": at_id,
            "linkId": linkId
        }
        post_data = json.dumps(post_data)
        self.client.post(url, data=post_data, content_type="application/json")
        self.assertTrue(IncomingMessage.objects.filter(africastalking_id=at_id).exists(), "Incoming msg obj not "
                                                                                          "created")
        self.assertTrue(Profile.objects.filter(telephone=self.phonenumber).exists(), "Profile obj not created")


