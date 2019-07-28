from celery import task
from django.conf import settings

from ujumbe.apps.messaging.models import OutgoingMessages
from ujumbe.apps.profiles.models import Profile
from ujumbe.apps.weather.models import Location, CurrentWeather, ForecastWeather



@task
def process_current_weather_request(phonenumber, detailed, location_name):
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    location = profile.location
    if location_name is not None:
        resolved_location = Location.try_resolve_location_by_name(name=location_name, phonenumber=phonenumber)
        if resolved_location is None:
            text = "Location named {} could not be determined. Please contact support.".format(location_name)
            OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)
            return
        else:
            location = resolved_location
    if location is None:
        response = "Please set profile default location or provide location name."
        OutgoingMessages.objects.create(phonenumber=phonenumber, text=response)
        return
    response = CurrentWeather.get_current_location_weather_text(location_id=location.id, detailed=detailed)
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=response)
    return


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
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=text)


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
    OutgoingMessages.objects.create(phonenumber=phonenumber, text=weather.detailed)
