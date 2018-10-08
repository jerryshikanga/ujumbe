from django.test import TestCase
from django_dynamic_fixture import G
from ujumbe.apps.weather.models import Location, CurrentWeather


# Create your tests here.
class ModelTests(TestCase):
    def test_instance_property_methods(self):
        location = G(Location)
        weather = G(CurrentWeather, location=location, )
        print("Description is " + weather.description)
