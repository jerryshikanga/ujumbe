from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from ujumbe.apps.africastalking.models import OutgoingMessages

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
        self.assertEqual(response.status_code, 201)  # should always return 200
