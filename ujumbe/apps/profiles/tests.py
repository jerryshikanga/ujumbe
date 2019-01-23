from mock import patch
from django.test import TestCase
from django_dynamic_fixture import G

from ujumbe.apps.profiles.models import Profile, AccountCharges


# Create your tests here.
class ChargeTests(TestCase):
    def test_balance_update(self):
        profile = G(Profile, balance=100)
        AccountCharges.objects.create(cost=10, currency_code="KES", profile=profile)
        self.assertEqual(profile.balance, 90)


class TelerivetTests(TestCase):
    @patch("ujumbe.apps.profiles.handlers.telerivet")
    def test_telerivet_sms(self, mock_telerivet):
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
        mock_telerivet.project.sendMessage.return_value = telerivet_response
