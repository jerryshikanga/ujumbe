from django.conf import settings
from ujumbe.apps.weather.models import ForecastWeather


def get_weather_forecast_periods():
    periods = ForecastWeather.PeriodOptions.choices
    string = ""
    counter = 0
    for period in periods:
        counter += 1
        text = str(period[0]).replace("-", " ")
        string += "{}. {} \n".format(counter, text)
    return string


def get_location_not_found_response(location_name: str = None):
    string = "Location"
    if location_name is not None:
        string += location_name
    string += "could not be determined. Please contact {} or {} to add it to our system.".format(
        settings.CUSTOMER_SUPPORT_PHONE, settings.CUSTOMER_SUPPORT_EMAIL)
    return string
