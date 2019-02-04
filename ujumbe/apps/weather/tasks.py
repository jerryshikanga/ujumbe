from celery import task
from django.conf import settings

from ujumbe.apps.profiles.tasks import send_sms
from ujumbe.apps.weather.models import Location, CurrentWeather, ForecastWeather


@task
def send_user_current_location_weather(phonenumber: str, location_id: int, detailed=False):
    location = Location.objects.get(id=location_id)
    if CurrentWeather.objects.filter(location=location).exists():
        weather = CurrentWeather.objects.filter(location=location).first()
        if not weather.is_valid():
            weather.retrieve(chanel=settings.DEFAULT_WEATHER_SOURCE)
    else:
        weather = CurrentWeather.objects.create(location=location)
        weather.retrieve(chanel=settings.DEFAULT_WEATHER_SOURCE)
    text = weather.detailed if detailed else weather.summary
    send_sms.delay(phonenumber=phonenumber, text=text)


@task
def send_user_forecast_weather_location(phonenumber: str, location_id: int, days: int):
    location = Location.objects.get(id=location_id)
    if ForecastWeather.objects.filter(location=location, days=days).exists():
        weather = ForecastWeather.objects.filter(location=location, days=days).first()
        if not weather.valid():
            weather.retrieve()
    else:
        weather = ForecastWeather.objects.create(location=location, days=days)
        weather.retrieve()
    send_sms.delay(phonenumber=phonenumber, text=weather.detailed)
