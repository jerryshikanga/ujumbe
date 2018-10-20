import os
import logging
import requests
from datetime import timedelta
from celery import task
from django.conf import settings
from django.utils import timezone
from ujumbe.apps.profiles.tasks import send_sms
from ujumbe.apps.weather.models import Location, CurrentWeather, ForecastWeather, LocationWeather
from ujumbe.apps.profiles.models import Subscription

open_weather_app_id = settings.OPEN_WEATHER_APP_ID


@task
def update_location_forecast_weather_via_open_weather(location_id: int, period_hours: int):
    """
    get the docs at https://openweathermap.org/forecast5
    """
    # currently open weather supports 5 day period only so period_hours param not used
    url = "https://api.openweathermap.org/data/2.5/forecast"
    location = Location.objects.get(id=location_id)
    data = {
        "APPID": open_weather_app_id,
        "units": "metric"
    }
    if location.owm_details_set:
        data.update({"id": location.owm_city_id})
    else:
        data.update({"q": location.get_name_with_country_code()})
    response = requests.get(url=url, params=data)
    if response.ok:
        response_json = response.json()

        if not location.owm_details_set:
            location.name = response_json["city"]["name"]
            location.owm_city_id = response_json["city"]["id"]
            location.longitude = response_json["city"]["coord"]["lon"]
            location.latitude = response_json["city"]["coord"]["lat"]
            location.save()

        weather, _ = ForecastWeather.objects.get_or_create(location=location, period=timedelta(hours=period_hours))

        weather.handler = LocationWeather.WeatherHandlers.openweather
        weather.forecast_time = response_json["list"]["dt"]
        weather.description = response_json["list"]["weather"]["description"]
        weather.temperature = response_json["list"]["main"]["temp"]
        weather.pressure = response_json["list"]["main"]["pressure"]
        weather.humidity = response_json["list"]["main"]["humidity"]
        weather.temp_min = response_json["list"]["main"]["temp_min"]
        weather.temp_max = response_json["list"]["main"]["temp_max"]
        # weather.visibility = response_json["visibility"] removed as it is not provided in api docs
        weather.wind_degree = response_json["list"]["wind"]["deg"]
        weather.wind_speed = response_json["list"]["wind"]["speed"]
        weather.clouds_all = response_json["list"]["clouds"]["all"]
        weather.rain = response_json["list"]["rain"]
        weather.save()
        return weather
    else:
        logging.warning(
            "Request at {} failed with status {} and message {}".format(str(timezone.now()), response.status_code,
                                                                        response.text))

    return None


@task
def update_location_current_weather_via_open_weather(location_id: int):
    """
    get the docs at https://openweathermap.org/current
    """
    location = Location.objects.get(id=location_id)
    url = "https://api.openweathermap.org/data/2.5/weather"
    data = {
        "APPID": open_weather_app_id,
        "units": "metric"
    }
    if location.owm_details_set:
        data.update({"id": location.owm_city_id})
    else:
        data.update({"q": location.get_name_with_country_code()})
    response = requests.get(url=url, params=data)

    if response.ok:
        response_json = response.json()
        if not location.owm_details_set:
            location.name = response_json["name"]
            location.owm_city_id = response_json["id"]
            location.longitude = response_json["coord"]["lon"]
            location.latitude = response_json["coord"]["lat"]
            location.save()
        weather, created = CurrentWeather.objects.get_or_create(location=location)
        weather.handler = LocationWeather.WeatherHandlers.openweather
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
        return weather
    else:
        logging.warning(
            "Request at {} failed with status {} and message {}".format(str(timezone.now()), response.status_code,
                                                                        response.text))
        return None


@task
def update_location_current_weather_via_netatmo(location_id: int):
    import patatmo
    credentials = {
        "password": settings.NETATMO_USERNAME,
        "username": settings.NETATMO_USERNAME,
        "client_id": settings.NETATMO_CLIENT_ID,
        "client_secret": settings.NETATMO_CLIENT_SECRET
    }
    authentication = patatmo.api.authentication.Authentication(
        credentials=credentials,
        tmpfile=os.path.join(settings.BASE_DIR, "temp", "temp_netatmo_auth.json")
    )
    # providing a path to a tmpfile is optionally.
    # If you do so, the tokens are stored there for later reuse,
    # e.g. next time you invoke this script.
    # This saves time because no new tokens have to be requested.
    # New tokens are then only requested if the old ones expire.

    # create a api client
    client = patatmo.api.client.NetatmoClient(authentication)

    location = Location.objects.get(id=location_id)
    # lat/lon outline of Hamburg/Germany
    region = {
        "lat_ne": location.lat_ne,
        "lat_sw": location.lat_sw,
        "lon_ne": location.lon_ne,
        "lon_sw": location.lon_sw,
    }
    # issue the API request
    region_data = client.Getpublicdata(region=region)

    # weather.handler = LocationWeather.WeatherHandlers.netatmo
    raise NotImplementedError("this function is not complete")


@task
def send_user_current_location_weather(phonenumber: str, location_id: int = None):
    if location_id is None:
        from ujumbe.apps.profiles.models import Profile
        profile = Profile.objects.filter(telephone=phonenumber).first()
        location = profile.location
    else:
        location = Location.objects.get(id=location_id)
    if CurrentWeather.objects.filter(location=location).exists():
        weather = CurrentWeather.objects.filter(location=location).first()
    else:
        CurrentWeather.objects.create(location=location)
        weather = update_location_current_weather_via_open_weather(location_id=location.id)
    if not weather.valid():
        update_location_current_weather_via_open_weather(location_id=location_id)
        weather.refresh_from_db()
    send_sms.delay(phonenumber=phonenumber, text=weather.detailed)


@task
def send_user_forecast_weather_location(phonenumber: str, location_id: int, period_hours: int):
    if location_id is None:
        from ujumbe.apps.profiles.models import Profile
        profile = Profile.objects.filter(telephone=phonenumber).first()
        location = profile.location
    else:
        location = Location.objects.get(id=location_id)
    weather = ForecastWeather.objects.filter(location=location, period=timedelta(hours=period_hours)).first()
    weather = weather if weather is not None else update_location_forecast_weather_via_open_weather(
        location_id=location.id,
        period_hours=period_hours)
    if not weather.valid():
        update_location_forecast_weather_via_open_weather(location_id=location_id, period_hours=period_hours)
        weather.refresh_from_db()
    send_sms.delay(phonenumber=phonenumber, text=weather.detailed)


@task
def send_user_subscriptions(phonenumber: str):
    subscriptions = Subscription.objects.for_phonenumber(phonenumber)
    text = ""
    for s in subscriptions:
        text += str(s)
    send_sms.delay(phonenumber=phonenumber, text=text)
