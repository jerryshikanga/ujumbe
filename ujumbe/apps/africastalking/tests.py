from mock import patch
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import G
from rest_framework.test import APITestCase

from ujumbe.apps.profiles.models import Profile
from ujumbe.apps.africastalking.models import OutgoingMessages, IncomingMessage
from ujumbe.apps.africastalking.tasks import process_incoming_messages

User = get_user_model()


# Create your tests here.
class TelerivetTests(APITestCase):
    @override_settings(TELERIVET_WEBHOOK_SECRET="secret")
    def test_sms_callback(self):
        message = OutgoingMessages.objects.create(
            **{"provider_id": "test", "delivery_status": "queued", "phonenumber": "+254727447101"})
        post_data = {
            "event": "send_status",
            "secret": "secret",
            "id": "test",
            "status": "delivered",
            "error_message": None
        }
        url = reverse("africastalking:telerivet_webhook_view")
        response = self.client.post(url, data=post_data, )
        message.refresh_from_db()
        self.assertEqual(message.delivery_status, "delivered")
        self.assertEqual(response.status_code, 200)  # should always return 200


class MessageProcessingTests(APITestCase):
    @patch("ujumbe.apps.africastalking.tasks.send_sms")
    @patch("ujumbe.apps.africastalking.tasks.create_customer_account")
    def test_same_shortcode_phonenumber(self, mock_create_account, mock_send_sms):
        G(IncomingMessage, processed=False, text="Register Jerry Shikanga", phonenumber="+254727447101",
          shortcode="+254727447101")
        mock_send_sms.return_value, mock_create_account.return_value = None, None
        responses = process_incoming_messages()
        self.assertEqual(len(responses), 0)

    @patch("ujumbe.apps.africastalking.tasks.send_sms")
    @patch("ujumbe.apps.africastalking.tasks.create_customer_account")
    def test_returned_response(self, mock_create_account, mock_send_sms):
        G(IncomingMessage, processed=False, text="Register Jerry Shikanga", phonenumber="+254727447101")
        mock_send_sms.return_value, mock_create_account.return_value = None, None
        responses = process_incoming_messages()
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0], "Your account will be created shortly. You will be notified via sms.")

    @patch("ujumbe.apps.africastalking.tasks.send_sms")
    @patch("ujumbe.apps.africastalking.tasks.create_customer_account")
    def test_invalid_keyword(self, mock_create_account, mock_send_sms):
        G(IncomingMessage, processed=False, text="Test Wrong Keyword", phonenumber="+254727447101")
        mock_send_sms.return_value, mock_create_account.return_value = None, None
        responses = process_incoming_messages()
        expected_response = "Your keyword test is invalid. Try again with either "
        self.assertTrue(str(responses[0]).startswith(expected_response))

    @patch("ujumbe.apps.africastalking.tasks.send_sms")
    @patch("ujumbe.apps.africastalking.tasks.create_customer_account")
    def test_unregistered_user_response(self, mock_create_account, mock_send_sms):
        G(IncomingMessage, processed=False, text="Subscribe", phonenumber="+254727447101")
        mock_send_sms.return_value, mock_create_account.return_value = None, None
        responses = process_incoming_messages()
        self.assertEqual(str(responses[0]), "Please create an account by sending REGISTER {first_name} {last_name}.")

    @patch("ujumbe.apps.africastalking.tasks.send_sms")
    @patch("ujumbe.apps.africastalking.tasks.create_customer_account")
    def test_reregister(self, mock_create_account, mock_send_sms):
        G(Profile, telephone="+254727447101")
        G(IncomingMessage, processed=False, text="Register Jerry Shikanga", phonenumber="+254727447101")
        mock_send_sms.return_value, mock_create_account.return_value = None, None
        responses = process_incoming_messages()
        self.assertEqual(str(responses[0]), "You are already registered.")
