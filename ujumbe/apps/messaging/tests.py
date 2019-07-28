import requests
import requests_mock
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import G
from mock import patch
from rest_framework.test import APITestCase

from ujumbe.apps.messaging.handlers import Telerivet
from ujumbe.apps.messaging.models import OutgoingMessages, IncomingMessage, MessageException
from ujumbe.apps.messaging.tasks import process_incoming_messages
from ujumbe.apps.profiles.models import Profile

User = get_user_model()


# Create your tests here.
class TelerivetTests(APITestCase):
    @override_settings(TELERIVET_WEBHOOK_SECRET="secret")
    def test_sms_callback(self):
        message = OutgoingMessages.objects.create(
            **{"provider_id": "test", "delivery_status": "queued", "phonenumber": "+254739936701"})
        post_data = {
            "event": "send_status",
            "secret": "secret",
            "id": "test",
            "status": "delivered",
            "error_message": None
        }
        url = reverse("messaging:telerivet_webhook_view")
        response = self.client.post(url, data=post_data, )
        message.refresh_from_db()
        self.assertEqual(message.delivery_status, "delivered")
        self.assertEqual(response.status_code, 200)  # should always return 200

    @patch("ujumbe.apps.messaging.handlers.requests.post")
    def test_telerivet_sms(self, mock_telerivet_request):
        telerivet_response = """
            {
                "id": "SMd9ff936d94df1f72", "phone_id": "PNf3ebae260670e677", "contact_id": "CT7631a03539e0ef2b",
                "direction": "outgoing", "status": "queued", "message_type": "sms", "source": "api",
                "time_created": 1547684822, "time_sent": null, "time_updated": 1547684822,
                "from_number": "254727447101",
                "to_number": "+254727447101", "content": "Hi there", "starred": false, "simulated": false, "vars": {},
                "external_id": null, "label_ids": [], "route_id": null, "broadcast_id": null, "service_id": null,
                "user_id": "UR32dbb2384cc385b4", "project_id": "PJ9e1257b6e08fba7e"}
            """
        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.register_uri('POST', 'mock://test.com', text=telerivet_response)
        mock_telerivet_request.return_value = session.post('mock://test.com')
        data = Telerivet.send_sms("+254727447101", "Test message")
        self.assertEqual(data["delivery_status"], "queued")
        self.assertEqual(data["provider_id"], "SMd9ff936d94df1f72")


class MessageProcessingTests(APITestCase):
    def test_same_shortcode_phonenumber(self):
        incoming_message = G(IncomingMessage, processed=False, text="Register Jerry Shikanga",
                             phonenumber="+254727447101", shortcode="+254727447101")
        with self.assertRaises(MessageException):
            responses = process_incoming_messages()
            message = OutgoingMessages.objects.first()
            error_text = "Short-code match phone number +254727447101 for message {}.".format(incoming_message.id)
            self.assertEqual(message.text, error_text)

    def test_returned_response(self):
        pass
        # G(IncomingMessage, processed=False, text="Register Jerry Shikanga", phonenumber="+254739936703")
        # process_incoming_messages()
        # message = OutgoingMessages.objects.first()
        # self.assertEqual(message.text, "Hello Jerry Shikanga, your account has been created successfully. Your "
        #

    def test_invalid_keyword(self):
        pass
        # message = G(IncomingMessage, processed=False, text="Test Wrong Keyword", phonenumber="+254739936704")
        # responses = process_incoming_messages()
        # expected_response = "Your keyword test is invalid. Try again with either "
        # self.assertTrue(str(responses[0]["text"]).startswith(expected_response))
        # message.refresh_from_db()
        # self.assertTrue(message.processed)

    def test_unregistered_user_response(self):
        pass

    def test_reregister(self):
        pass
        # G(Profile, telephone="+254739936706")
        # G(IncomingMessage, processed=False, text="Register Jerry Shikanga", phonenumber="+254739936706")
        # responses = process_incoming_messages()
        # self.assertEqual(str(responses[0]["text"]), "You are already registered.")

    def test_language_set_valid(self):
        pass

    def test_language_set_invalid(self):
        pass

    # @patch("ujumbe.apps.messaging.tasks.send_bulk_sms")
    # def test_default_profile_is_set_if_weather_is_requested_but_no_profile_set(self, mock_send_sms):
    #     G(Profile, telephone="+254739936708")
    #     G(IncomingMessage, processed=False, text="Weather*Detailed*Naivasha", phonenumber="+254739936708")
    #     mock_send_sms.return_value = None
    #     responses = process_incoming_messages()
    #     self.assertIn("Your default location has been set to Naivasha.", responses[0])

    # @patch("ujumbe.apps.messaging.tasks.send_bulk_sms")
    # def test_weather(self, mock_send_sms):
    #     mock_send_sms.return_value.return_value = None
    #     phone = "+254739936707"
    #     G(Profile, telephone=phone)
    #     country = G(Country, alpha2="KE", alpha3="KEN", name="Kenya")
    #     location = G(Location, country=country, name="Naivasha")
    #     weather = G(CurrentWeather, location=location)
    #     G(IncomingMessage, processed=False, text="Weather Detailed Naivasha", phonenumber=phone)
    #     responses = process_incoming_messages()
    #     self.assertEqual(str(responses[0]), weather.detailed)


class TranslationTests(APITestCase):
    @patch("ujumbe.apps.messaging.tasks.requests.get")
    def test_yandex_translate(self, mock_yandex_response):
        response = """
        <?xml version="1.0" encoding="utf-8"?>
        <?xml version="1.0" encoding="utf-8"?>
            <Translation code="200" lang="en-sw"><text>Hali ya hewa ya Kakamega ni mawingu</text>
            </Translation>
        """
        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.register_uri('GET', 'mock://test.com', text=response)
        mock_yandex_response.return_value = session.get('mock://test.com')
        from ujumbe.apps.messaging.tasks import translate_text
        translated = translate_text("en", "sw", "Weather Kakamega is cloudy")
        self.assertEqual(translated, "Hali ya hewa ya Kakamega ni mawingu")
