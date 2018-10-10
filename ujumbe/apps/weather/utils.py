from django.conf import settings


def get_weather_forecast_periods():
    periods = []
    periods.append("1 Hour")
    periods.append("12 Hours")
    periods.append("1 Day")
    periods.append("1 Week")
    periods.append("1 Month")

    string = ""
    counter = 0
    for period in periods:
        string += "{}. {}\n".format(counter, period)
        counter += 1
    return string


def get_location_not_found_response(location_name: str = None):
    string = "Location"
    if location_name is not None:
        string += location_name
    string += "could not be determined. Please contact {} or {} to add it to our system.".format(
        settings.CUSTOMER_SUPPORT_PHONE, settings.CUSTOMER_SUPPORT_EMAIL)
    return string
