import logging
import datetime

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseHandler(object):
    def get_current_weather(self, latitude, longitude):
        raise NotImplementedError("This method must be implemented")

    def get_forecast_weather(self, latitude, longitude):
        raise NotImplementedError("This method must be implemented")


class NetAtmo(BaseHandler):
    pass


class OpenWeather(BaseHandler):
    """
    Docs at https://openweathermap.org/current
    """
    def get_current_weather(self, latitude, longitude):
        url = "https://api.openweathermap.org/data/2.5/weather"
        data = {
            "APPID": settings.OPEN_WEATHER_APP_ID,
            "units": "metric",
            "lat": latitude,
            "lon": longitude
        }
        response = requests.get(url=url, params=data)

        try:
            if response.ok:
                response_json = response.json()
                logger.warning("OpenWeather response {}".format(str(response_json)))
                print("OpenWeather response {}".format(str(response_json)))
                weather = dict()
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
                weather["summary"] = response_json["weather"][0]["description"]
                weather["temperature"] = response_json["main"]["temp"]
                weather["pressure"] = response_json["main"]["pressure"]
                weather["humidity"] = response_json["main"]["humidity"]
                weather["temp_min"] = response_json["main"]["temp_min"]
                weather["temp_max"] = response_json["main"]["temp_max"]
                weather["visibility"] = response_json["visibility"]
                weather["wind_speed"] = response_json["wind"]["speed"]
                weather["wind_degree"] = response_json["wind"]["deg"]
                weather["clouds_all"] = response_json["clouds"]["all"]
                return weather
            else:
                logger.warning(
                    "Request at {} failed with status {} and message {}".format(str(datetime.datetime.now()),
                                                                                response.status_code,
                                                                                response.text))
                return None
        except Exception as e:
            logger.error(str(e))
            return None

    def get_forecast_weather(self, latitude, longitude, days: int):
        url = "http://api.openweathermap.org/data/2.5/forecast/daily"
        data = {
            "APPID": settings.OPEN_WEATHER_APP_ID,
            "units": "metric",
            "lat": latitude,
            "lon": longitude,
            "cnt": days
        }
        response = requests.get(url=url, params=data)
        if response.ok:
            response_json = response.json()
            weather = dict()
            weather["forecast_time"] = response_json["list"]["dt"]
            weather["summary"] = response_json["weather"]["main"]
            weather["temperature"] = response_json["main"]["temp"]
            weather["pressure"] = response_json["main"]["pressure"]
            weather["humidity"] = response_json["main"]["humidity"]
            weather["temp_min"] = response_json["main"]["temp_min"]
            weather["temp_max"] = response_json["main"]["temp_max"]
            weather["visibility"] = response_json["visibility"]
            weather["wind_speed"] = response_json["wind"]["speed"]
            weather["wind_degree"] = response_json["wind"]["deg"]
            weather["clouds_all"] = response_json["clouds"]["all"]
            return weather
        else:
            logger.warning(
                "Request at {} failed with status {} and message {}".format(str(timezone.now()), response.status_code,
                                                                            response.text))

        return None


class AccuWeather(BaseHandler):
    def get_current_weather(self, accuweather_city_id: int):
        url = "http://dataservice.accuweather.com/currentconditions/v1/{}".format(accuweather_city_id)
        params = {
            "apikey": settings.ACCUWEATHER_API_KEY,
            "details": "true",
            "language": "en-us",
        }
        response = requests.get(url=url, params=params).json()
        response = response[0]

        weather = dict()
        weather["summary"] = response["WeatherText"]
        weather["temperature"] = response["RealFeelTemperature"]["Metric"]["Value"]
        weather["pressure"] = response["Pressure"]["Metric"]["Value"]
        weather["humidity"] = response["RelativeHumidity"]
        weather["temp_min"] = response["TemperatureSummary"]["Past6HourRange"]["Minimum"]["Metric"]["Value"]
        weather["temp_max"] = response["TemperatureSummary"]["Past6HourRange"]["Maximum"]["Metric"]["Value"]
        weather["visibility"] = response["Visibility"]["Metric"]["Value"]
        weather["wind_speed"] = response["WindGust"]["Speed"]["Metric"]["Value"]
        weather["wind_degree"] = response["Wind"]["Direction"]["Degrees"]
        weather["clouds_all"] = response["CloudCover"]
        weather["rain"] = response["PrecipitationSummary"]["Precipitation"]["Metric"]["Value"]

        return weather

    def get_forecast_weather(self, accuweather_city_id: int, days: int):
        url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/{}".format(accuweather_city_id)
        params = {
            "apikey": settings.ACCUWEATHER_API_KEY,
            "details": "true",
            "language": "en-us",
            "metric": "true"
        }
        response = requests.get(url=url, params=params).json()
        forecast_days = response["DailyForecasts"]
        for forecast_day in forecast_days:
            timestr = forecast_day["Date"]
            timestr = timestr.replace(":00+03:00", "") if timestr.endswith(":00+03:00") else timestr # TODO : Use pattern matching to drop, this will only work for Timezonennairobi
            time = datetime.datetime.strptime(timestr.replace("T", " "), "%Y-%m-%d %H:%M")
            days_forward = (time - datetime.datetime.now()).days
            if days == days_forward:
                weather = dict()
                weather["summary"] = response["Day"]["LongPhrase"]
                # weather["temperature"] = response["RealFeelTemperature"]["Metric"]["Value"]
                # weather["pressure"] = response["Pressure"]["Metric"]["Value"]
                # weather["humidity"] = response["RelativeHumidity"]
                weather["temp_min"] = response["Day"]["Temperature"]["Minimum"]["Value"]
                weather["temp_max"] = response["Day"]["Temperature"]["Maximum"]["Value"]
                # weather["visibility"] = response["Visibility"]["Metric"]["Value"]
                weather["wind_speed"] = response["Day"]["Wind"]["Speed"]["Value"]
                weather["wind_degree"] = response["Day"]["Wind"]["Direction"]["Degrees"]
                weather["clouds_all"] = response["Day"]["CloudCover"]
                weather["rain"] = response["Day"]["Rain"]["Value"]
                return weather
