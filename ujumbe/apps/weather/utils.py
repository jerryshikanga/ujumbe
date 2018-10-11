from django.conf import settings
import humanize
from datetime import timedelta

ForecastPeriods = [
    timedelta(days=5),
    timedelta(days=16),
]


def get_ussd_formatted_weather_forecast_periods():
    string = ""
    counter = 0
    for option in ForecastPeriods:
        string += "{}. {}.\n".format(counter, humanize.naturaldelta(option))
        counter += 1
    return string


def get_location_not_found_response(location_name: str = None):
    string = "Location"
    if location_name is not None:
        string += location_name
    string += "could not be determined. Please contact {} or {} to add it to our system.".format(
        settings.CUSTOMER_SUPPORT_PHONE, settings.CUSTOMER_SUPPORT_EMAIL)
    return string
