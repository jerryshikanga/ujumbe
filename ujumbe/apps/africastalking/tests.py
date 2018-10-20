from django.test import TestCase
from ujumbe.apps.africastalking.models import IncomingMessage
from ujumbe.apps.profiles.models import Profile
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.urls import reverse
import json
import re
import datetime
from django_dynamic_fixture import G
from ujumbe.apps.weather.utils import get_location_not_found_response

User = get_user_model()


# Create your tests here.
class MessageTests(TestCase):
    def setUp(self):
        self.phonenumber = "+254792651659"
        self.at_shortcode = 20880

    def test_register_view(self):
        text = "REGISTER Martin Miano"
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
        user = G(User)
        Profile.objects.create(user=user, telephone=self.phonenumber)
        text = "TEST JERRY SHIKANGA"
        at_id = get_random_string(10)
        link_id = get_random_string(15)
        time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        url = reverse("africastalking:at_message_callback_view")
        post_data = {
            "from": self.phonenumber,
            "to": self.at_shortcode,
            "text": text,
            "date": time,
            "id": at_id,
            "linkId": link_id
        }
        post_data = json.dumps(post_data)
        self.client.post(url, data=post_data, content_type="application/json")
        self.assertTrue(IncomingMessage.objects.filter(africastalking_id=at_id).exists(), "Incoming msg obj not "
                                                                                          "created")
        self.assertTrue(Profile.objects.filter(telephone=self.phonenumber).exists(), "Profile obj not created")


class UssdTests(TestCase):
    def setUp(self):
        from scripts import init_db
        init_db.run()
        self.post_data = dict(sessionId=get_random_string(length=10), serviceCode="20880", phoneNumber="", text="")
        self.post_headers = {
            "content-type": "application/json"
        }
        self.at_ussd_callback_url = reverse("africastalking:at_ussd_callback_view")

    def test_re_pattern_match(self):
        code = "1*2*kakamega"
        match = re.match(r"\d\*\d\*\w+", code)
        self.assertIsNotNone(match)
        code = "2*1*kakamega*1"
        match = re.match(r"2\*1\*\w+\*\d", code)
        self.assertIsNotNone(match)

    def test_register(self):
        # first step, user has no a/c.
        self.post_data["text"] = ""
        self.post_data["phoneNumber"] = "+254727447101"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)
        self.assertContains(response, "You don't have an account")

        # now user chooses register option
        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0*"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
        #
        # self.post_data["text"] = "0"
        # response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
        #                             content_type="application/json")
        # self.assertEqual(int(response.status_code), 200)
