from django.test import TestCase
from ujumbe.apps.africastalking.models import IncomingMessage, OutgoingMessages, Message
from ujumbe.apps.profiles.models import Profile
from django.contrib.auth import get_user_model
import random
from django.urls import reverse
import json
import re
import datetime
from django_dynamic_fixture import G
from mock import patch
from ujumbe.apps.profiles.tasks import send_sms
from django.utils.crypto import get_random_string
from django.urls import reverse

User = get_user_model()


def mocked_at_send_sms(*args, **kwargs):
    return {
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 0.8000 Message parts: 1",
            "Recipients": [
                {
                    "statusCode": 101,
                    "number": "+254727447101",
                    "cost": "KES 0.8000",
                    "messageId": get_random_string(length=12),
                    "status": "Success"
                },
            ]
        }
    }


# Create your tests here.
class IncomingMessageTests(TestCase):
    def setUp(self):
        random.seed(datetime.datetime.now())
        self.phonenumber = "+2547{}".format(random.randint(10000000, 99999999))
        self.at_shortcode = 20880

    def test_register_view(self):
        text = "REGISTER Martin Miano"
        at_id = get_random_string(10)
        url = reverse("africastalking:incoming_message_callback")
        post_data = {
            "from": self.phonenumber,
            "to": self.at_shortcode,
            "text": text,
            "date": (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "id": at_id,
            "linkId": get_random_string(15)
        }
        post_data = json.dumps(post_data)
        self.client.post(url, data=post_data, content_type="application/json")
        self.assertTrue(IncomingMessage.objects.filter(provider_id=at_id).exists())

    def test_wrong_keyword(self):
        user = G(User)
        Profile.objects.create(user=user, telephone=self.phonenumber)
        text = "TEST JERRY SHIKANGA"
        at_id = get_random_string(10)
        link_id = get_random_string(15)
        time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        post_data = {
            "from": self.phonenumber,
            "to": self.at_shortcode,
            "text": text,
            "date": time,
            "id": at_id,
            "linkId": link_id
        }
        self.client.post(reverse("africastalking:incoming_message_callback"), data=json.dumps(post_data),
                         content_type="application/json")
        self.assertTrue(IncomingMessage.objects.filter(provider_id=at_id).exists())


class OutgoingMessageTests(TestCase):
    @patch("ujumbe.apps.profiles.tasks.africastalking.SMSService.send", side_effect=mocked_at_send_sms)
    def test_incoming_sms_callback(self, mock_at_send_sms):
        random.seed(datetime.datetime.now())
        phonenumber = "+2547{}".format(random.randint(10000000, 99999999))
        message_content = "Test"
        message = send_sms(phonenumber=phonenumber, text=message_content)
        self.assertIsNotNone(OutgoingMessages.objects.filter(provider_id=message.provider_id).filter(
            handler=Message.MessageProviders.Africastalking))
        data = {
            "phoneNumber": phonenumber,
            "status": "success",
            "id": message.provider_id,
            "networkCode": 63902
        }
        response = self.client.post(reverse("africastalking:outgoing_message_callback"), data=json.dumps(data),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_incoming_sms_callback_failure(self):
        random.seed(datetime.datetime.now())
        data = {
            "phoneNumber": "+2547{}".format(random.randint(10000000, 99999999)),
            "status": "success",
            "id": "123456",
            "networkCode": 63902
        }
        response = self.client.post(reverse("africastalking:outgoing_message_callback"), data=json.dumps(data),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)


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
        random.seed(datetime.datetime.now())
        self.post_data["phoneNumber"] = "+2547{}".format(random.randint(10000000, 99999999))
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)
        self.assertIn("You don't have an account", str(response.content))

        # now user chooses register option
        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0*"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)

        self.post_data["text"] = "0"
        response = self.client.post(self.at_ussd_callback_url, data=json.dumps(self.post_data),
                                    content_type="application/json")
        self.assertEqual(int(response.status_code), 200)


class TelerivetTests(TestCase):
    def test_sms_callback(self):
        post_data = {
            "event": "send_status",
            "secret": "ALNTFZUQWERWUE7RZGNQH4A6CEK2RDHZ"
        }
        url = reverse("africastalking:telerivet_webhook_view")
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 200)  # should always return 200
