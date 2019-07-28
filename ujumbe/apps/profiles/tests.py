from django.test import TestCase
from django_dynamic_fixture import G

from ujumbe.apps.profiles.models import Profile, AccountCharges


# Create your tests here.
class ChargeTests(TestCase):
    def test_balance_update(self):
        profile = G(Profile, balance=100, telephone="+254727447101")
        AccountCharges.objects.create(cost=10, currency_code="KES", profile=profile)
        self.assertEqual(profile.balance, 90)
