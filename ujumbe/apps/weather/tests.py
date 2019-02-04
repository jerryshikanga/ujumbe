import datetime
import json

from django.test import TestCase
from django_dynamic_fixture import G
from mock import patch
import requests_mock
import requests

from ujumbe.apps.weather.models import Location, CurrentWeather


# Create your tests here.
class ModelTests(TestCase):
    def test_instance_property_methods(self):
        location = G(Location)
        weather = G(CurrentWeather, location=location, )

    def test_current_weather_validity(self):
        hours5_ago = datetime.datetime.now() - datetime.timedelta(hours=5)
        weather1 = G(CurrentWeather, created=hours5_ago, modified=hours5_ago)
        hours1_ago = datetime.datetime.now() - datetime.timedelta(hours=0.75)
        weather2 = G(CurrentWeather, created=hours1_ago, modified=hours1_ago)
        self.assertFalse(weather1.is_valid())
        self.assertTrue(weather2.is_valid())

    @patch("ujumbe.apps.weather.handlers.requests.get")
    def test_open_weather(self, mock_requests_get):
        d = {
            'coord': {
                'lon': 37.01,
                'lat': -1.1
            },
            'weather':
                [
                    {
                        'id': 800,
                        'main': 'Clear',
                        'description': 'clear sky',
                        'icon': '01n'
                    }
                ],
            'base': 'stations',
            'main': {
                'temp': 20,
                'pressure': 1021,
                'humidity': 68,
                'temp_min': 20,
                'temp_max': 20
            },
            'visibility': 10000,
            'wind': {
                'speed': 4.1,
                'deg': 50
            },
            'clouds': {
                'all': 0
            },
            'dt': 1549317600,
            'sys': {
                'type': 1,
                'id': 2543,
                'message': 0.0038,
                'country': 'KE',
                'sunrise': 1549251670,
                'sunset': 1549295440
            },
            'id': 179330,
            'name': 'Thika',
            'cod': 200
        }
        adapter = requests_mock.Adapter()
        session = requests.Session()
        session.mount('mock', adapter)
        adapter.register_uri('GET', 'mock://test.com', text=json.dumps(d))
        mock_requests_get.return_value = session.get('mock://test.com')
        from ujumbe.apps.weather.handlers import OpenWeather
        weather = OpenWeather().get_current_weather(1, 2)
        data = {
            "summary": "clear sky",
            "temperature": 20,
            "pressure": 1021,
            "humidity": 68,
            "temp_min": 20,
            "temp_max": 20,
            "visibility": 10000,
            "wind_speed": 4.1,
            "wind_degree": 50,
            "clouds_all": 0
        }
        self.assertEqual(weather, data)
