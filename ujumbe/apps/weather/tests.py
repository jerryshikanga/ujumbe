from django.test import TestCase
import datetime
from ujumbe.apps.weather.models import Location, CurrentWeather
from django_dynamic_fixture import G


# Create your tests here.
class ModelTests(TestCase):
    def test_instance_property_methods(self):
        location = G(Location)
        weather = G(CurrentWeather, location=location, )
        print("Description is " + weather.description)

    def test_current_weather_validity(self):
        hours5_ago = datetime.datetime.now()-datetime.timedelta(hours=5)
        weather1 = G(CurrentWeather, created=hours5_ago, modified=hours5_ago)
        hours2_ago = datetime.datetime.now() - datetime.timedelta(hours=2)
        weather2 = G(CurrentWeather, created=hours2_ago, modified=hours2_ago)
        self.assertFalse(weather1.valid())
        self.assertTrue(weather2.valid())
