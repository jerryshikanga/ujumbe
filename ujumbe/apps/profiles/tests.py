from django.test import TestCase
from ujumbe.apps.profiles.models import Profile, AccountCharges
from django_dynamic_fixture import G


# Create your tests here.
class ChargeTests(TestCase):
    def test_balance_update(self):
        profile = G(Profile, balance=100)
        AccountCharges.objects.create(cost=10, currency_code="KES", profile=profile)
        self.assertEqual(profile.balance, 90)
