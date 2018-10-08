import logging
import requests
from celery import task
from django.conf import settings
from django.utils import timezone

from ujumbe.apps.weather.models import Location, CurrentWeather

open_weather_app_id = settings.OPEN_WEATHER_APP_ID


@task
def get_current_weather_by_location_id(latitude: int, longitude: int):
    url = "api.openweathermap.org/data/2.5/weather"
    data = {
        "lat": latitude,
        "lon": longitude,
        "APPID": open_weather_app_id,
        "units": "metric"
    }
    response = requests.get(url=url, params=data)
    timenow = timezone.now()
    if response.ok:
        response_json = response.json()
        location, created = Location.objects.get_or_create(
            latitude=response_json["coord"]["lat"],
            longitude=response_json["coord"]["lon"]
        )
        weather, created = CurrentWeather.objects.get_or_create(location=location)
        weather.description = response_json["weather"]["main"]
        weather.temperature = response_json["main"]["temp"]
        weather.pressure = response_json["main"]["pressure"]
        weather.humidity = response_json["main"]["humidity"]
        weather.temp_min = response_json["main"]["temp_min"]
        weather.temp_max = response_json["main"]["temp_max"]
        weather.visibility = response_json["visibility"]
        weather.wind_degree = response_json["wind"]["deg"]
        weather.wind_speed = response_json["wind"]["speed"]
        weather.clouds_all = response_json["clouds"]["all"]
        weather.save()

    else:
        logging.warning("Request at {} failed with status {} and message {}".format(str(timenow), response.status_code,
                                                                                    response.text))


@task
def update_location_current_weather(location: Location):
    url = "https://api.openweathermap.org/data/2.5/weather"
    data = {
        "q": location.get_name_with_country_code(),
        "APPID": open_weather_app_id,
        "units": "metric"
    }
    response = requests.get(url=url, params=data)
    timenow = timezone.now()
    if response.ok:
        response_json = response.json()
        location, created = Location.objects.get_or_create(
            latitude=response_json["coord"]["lat"],
            longitude=response_json["coord"]["lon"]
        )
        weather, created = CurrentWeather.objects.get_or_create(location=location)
        weather.description = response_json["weather"]["main"]
        weather.temperature = response_json["main"]["temp"]
        weather.pressure = response_json["main"]["pressure"]
        weather.humidity = response_json["main"]["humidity"]
        weather.temp_min = response_json["main"]["temp_min"]
        weather.temp_max = response_json["main"]["temp_max"]
        weather.visibility = response_json["visibility"]
        weather.wind_degree = response_json["wind"]["deg"]
        weather.wind_speed = response_json["wind"]["speed"]
        weather.clouds_all = response_json["clouds"]["all"]
        weather.save()

    else:
        logging.warning("Request at {} failed with status {} and message {}".format(str(timenow), response.status_code,
                                                                                    response.text))


@task
def run_weather_checks_by_name():
    inhabited_locations_with_active_subscriptions = Location.objects.with_active_subscription()
    for location in inhabited_locations_with_active_subscriptions:
        try:
            update_location_current_weather(location)
            message = "{} for {} run successfully".format(str(run_weather_checks_by_name.__name__), str(location))
            print(message)
            logging.info(message)
        except Exception as e:
            message = "Failed to run {} for {}. Error {}".format(str(run_weather_checks_by_name.__name__), str(location), str(e))
            print(message)
            logging.warning(message)


