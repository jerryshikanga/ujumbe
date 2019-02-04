import datetime
import logging

import googlemaps
import requests
from author.decorators import with_author
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from djchoices import ChoiceItem, DjangoChoices

from ujumbe.apps.weather.handlers import OpenWeather, AccuWeather, NetAtmo


logger = logging.getLogger(__name__)


# Create your models here.
@with_author
class Country(TimeStampedModel):
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    alpha2 = models.CharField(max_length=2, null=False, blank=False, unique=True)
    alpha3 = models.CharField(max_length=3, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Countries"
        verbose_name = "Country"
        ordering = ["name", ]


class LocationManager(models.Manager):
    def with_active_subscription(self):
        return super(LocationManager, self).get_queryset().filter(subscription__active=True)

    def in_country(self, country: Country):
        return super(LocationManager, self).get_queryset().filter(country=country)


@with_author
class Location(TimeStampedModel):
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    altitude = models.FloatField(blank=True, null=True)
    bounds_northeast_latitude = models.FloatField(blank=True, null=True)
    bounds_southwest_latitude = models.FloatField(blank=True, null=True)
    bounds_northeast_longitude = models.FloatField(blank=True, null=True)
    bounds_southwest_longitude = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    owm_city_id = models.IntegerField(default=0, null=True, blank=True)
    googlemaps_place_id = models.CharField(max_length=255, null=True, blank=True)
    accuweather_city_id = models.CharField(max_length=255, null=True, blank=True)

    objects = LocationManager()

    class Meta(object):
        unique_together = ["latitude", "longitude"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ["name", ]

    def __str__(self):
        return "{} Latitude : {}, Longitude : {}".format(self.name, self.latitude, self.longitude)

    def get_name_with_country_code(self):
        if self.country is None:
            raise ValueError("Country cannot be blank")
        else:
            return "{}, {}".format(self.name, self.country.alpha2)

    def get_name_with_country_name(self):
        if self.country is None:
            raise ValueError("Country cannot be blank")
        else:
            return "{}, {}".format(self.name, self.country.name)

    def set_accuweather_city_id(self):
        # we currently use google maps to determine lat and lon so if gmaps id is set then they are valid
        if self.googlemaps_place_id is None:
            self.geocode_location_by_google_maps()
        url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        params = {
            "apikey": settings.ACCUWEATHER_API_KEY,
            "details": "false",
            "q": "{},{}".format(self.latitude, self.longitude),
            "language": "en-us",
            "topelevel": "false"
        }
        response = requests.get(url=url, params=params).json()
        self.accuweather_city_id = response["Key"]
        self.save()

    def geocode_location_by_google_maps(self):
        gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
        geocode_result = gmaps.geocode(self.get_name_with_country_name())
        try:
            result = geocode_result[0]
            geometry = result["geometry"]
            location = geometry["location"]
            bounds = geometry["bounds"]

            self.latitude = location["lat"]
            self.longitude = location["lng"]
            self.bounds_northeast_longitude = bounds["northeast"]["lng"]
            self.bounds_southwest_longitude = bounds["southwest"]["lng"]
            self.bounds_northeast_latitude = bounds["northeast"]["lat"]
            self.bounds_southwest_latitude = bounds["southwest"]["lat"]

            self.googlemaps_place_id = result["place_id"]

            self.save()

        except Exception as e:
            logging.error(str(e))

    @classmethod
    def try_resolve_location_by_name(cls, name: str, phonenumber: str):
        from phone_iso3166.country import phone_country
        country = Country.objects.filter(alpha2=phone_country(phonenumber)).first()
        location = Location.objects.in_country(country).filter(name__icontains=name).first()
        if location is not None:
            return location

        gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
        try:
            name += ", " + country.name
            geocode_result = gmaps.geocode(name)
            result = geocode_result[0]
            geometry = result["geometry"]
            location = geometry["location"]
            bounds = geometry["bounds"]
            address_components = result["address_components"]
            address = address_components[0]

            location_obj = Location()
            location_obj.name = address["long_name"]
            location_obj.country = country
            location_obj.latitude = location["lat"]
            location_obj.longitude = location["lng"]
            location_obj.bounds_northeast_longitude = bounds["northeast"]["lng"]
            location_obj.bounds_southwest_longitude = bounds["southwest"]["lng"]
            location_obj.bounds_northeast_latitude = bounds["northeast"]["lat"]
            location_obj.bounds_southwest_latitude = bounds["southwest"]["lat"]

            location_obj.googlemaps_place_id = result["place_id"]

            location_obj.save()
            return location_obj
        except Exception as e:
            logging.error(str(e))
            return None


@receiver(signal=post_save, sender=Location)
def check_and_update_location_by_google_maps_and_accuweather(sender, instance, created, **kwargs):
    if created:
        if instance.googlemaps_place_id is None:
            instance.geocode_location_by_google_maps()
            instance.set_accuweather_city_id()
    return


class LocationWeather(TimeStampedModel):
    class WeatherHandlers(DjangoChoices):
        netatmo = ChoiceItem("NETATMO")
        openweather = ChoiceItem("OPENWEATHER")
        accuweather = ChoiceItem("AccuWeather")

    handler = models.CharField(blank=False, null=False, choices=WeatherHandlers.choices, max_length=30)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.CharField(max_length=255, null=False, blank=False, default="")
    temperature = models.IntegerField(default=0, null=False, blank=False)
    pressure = models.IntegerField(default=0, null=False, blank=False)
    humidity = models.IntegerField(default=0, null=False, blank=False)
    temp_min = models.IntegerField(default=0, null=False, blank=False)
    temp_max = models.IntegerField(default=0, null=False, blank=False)
    visibility = models.IntegerField(default=0, null=True, blank=True)
    wind_speed = models.IntegerField(default=0, null=False, blank=False)
    wind_degree = models.IntegerField(default=0, null=False, blank=False)
    clouds_all = models.IntegerField(default=0, null=False, blank=False)
    rain = models.FloatField(null=True, blank=True, default=0)

    class Meta(object):
        abstract = True
        verbose_name = "Weather"
        verbose_name_plural = "Weather"

    def is_valid(self):
        raise NotImplementedError("The valid method should be implemented")

    def retrieve(self, chanel):
        raise NotImplementedError("The retrive method should be implemented")

    def __str__(self):
        return "Location {}, Summary {}, Temperature {}, Pressure {}, Humidity {}, Minimum temperature {} Maximum " \
               "temperature {} Visibility {} Wind Speed {} Cloud Cover {} Last Checked {}".format(self.location,
                                                                                                  self.summary,
                                                                                                  self.temperature,
                                                                                                  self.pressure,
                                                                                                  self.humidity,
                                                                                                  self.temp_min,
                                                                                                  self.temp_max,
                                                                                                  self.visibility,
                                                                                                  self.wind_speed,
                                                                                                  self.clouds_all,
                                                                                                  self.modified)

    @property
    def last_check_time(self):
        return self.modified.strftime("%Y-%m-%d %H:%M")

    @property
    def description(self):
        return "Location {} Summary {} Last Checked {}".format(self.location, self.summary, self.last_check_time)

    @property
    def detailed(self):
        return "Location {}, Summary {}, Temperature {}, Pressure {}, Humidity {}, Minimum temperature {} Maximum " \
               "temperature {} Visibility {} Wind Speed {} Cloud Cover {} Last Checked {}".format(self.location,
                                                                                                  self.summary,
                                                                                                  self.temperature,
                                                                                                  self.pressure,
                                                                                                  self.humidity,
                                                                                                  self.temp_min,
                                                                                                  self.temp_max,
                                                                                                  self.visibility,
                                                                                                  self.wind_speed,
                                                                                                  self.clouds_all,
                                                                                                  self.modified)


class CurrentWeather(LocationWeather):
    class Meta(object):
        verbose_name = "Current Weather"
        verbose_name_plural = "Current Weather"

    def is_valid(self):
        return (datetime.datetime.now() - datetime.timedelta(hours=1)) <= self.modified

    @property
    def description(self):
        return "Current weather {}".format(super(CurrentWeather, self).description)

    @property
    def detailed(self):
        return "Current weather {}".format(super(CurrentWeather, self).detailed)

    @staticmethod
    def get_current_location_weather_text(location_id: int, detailed: bool = False):
        location = Location.objects.get(id=location_id)
        if CurrentWeather.objects.filter(location=location).exists():
            weather = CurrentWeather.objects.filter(location=location).first()
            weather = weather if weather.is_valid() else weather.retrieve(chanel=settings.DEFAULT_WEATHER_SOURCE)
        else:
            weather = CurrentWeather.objects.create(location=location)
            weather = weather.retrieve(chanel=settings.DEFAULT_WEATHER_SOURCE)
        return weather.detailed if detailed else weather.summary

    def retrieve(self, chanel):
        if chanel == LocationWeather.WeatherHandlers.accuweather:
            self.handler = LocationWeather.WeatherHandlers.accuweather
            if self.location.accuweather_city_id is None:
                self.location.set_accuweather_city_id()
            weather = AccuWeather().get_current_weather(accuweather_city_id=self.location.accuweather_city_id)
        elif chanel == LocationWeather.WeatherHandlers.openweather:
            self.handler = LocationWeather.WeatherHandlers.openweather
            weather = OpenWeather().get_current_weather(latitude=self.location.latitude,
                                                        longitude=self.location.longitude)
        elif chanel == LocationWeather.WeatherHandlers.netatmo:
            self.handler = LocationWeather.WeatherHandlers.netatmo
            weather = NetAtmo().get_current_weather(latitude=self.location.latitude, longitude=self.location.longitude)
        else:
            raise ValueError("Unknown chanel")
        self.summary = weather["summary"]
        self.temperature = weather["temperature"]
        self.pressure = weather["pressure"]
        self.humidity = weather["humidity"]
        self.temp_min = weather["temp_min"]
        self.temp_max = weather["temp_max"]
        self.visibility = weather["visibility"]
        self.wind_speed = weather["wind_speed"]
        self.wind_degree = weather["wind_degree"]
        self.clouds_all = weather["clouds_all"]
        # self.rain = weather["rain"]
        self.save()

        return self


class ForecastWeather(LocationWeather):
    days = models.IntegerField(null=False, blank=False)
    forecast_time = models.DateTimeField(null=False, blank=False, default=timezone.now)

    class Meta(object):
        verbose_name = "Forecast Weather"
        verbose_name_plural = "Forecast Weather"

    @property
    def description(self):
        return "Forecast for {}, {}".format(self.days, super(ForecastWeather, self).description)

    @property
    def detailed(self):
        return "Forecast for {}, {}".format(self.days, super(ForecastWeather, self).detailed)

    def is_valid(self):
        return datetime.datetime.now() <= (self.forecast_time + self.days)

    def retrieve(self, chanel=settings.DEFAULT_WEATHER_SOURCE):
        if chanel == LocationWeather.WeatherHandlers.accuweather:
            self.handler = LocationWeather.WeatherHandlers.accuweather
            weather = AccuWeather().get_forecast_weather(location_id=self.id, days=self.days)
        elif chanel == LocationWeather.WeatherHandlers.openweather:
            self.handler = LocationWeather.WeatherHandlers.openweather
            weather = OpenWeather().get_forecast_weather(location_id=self.id, days=self.days)
        elif chanel == LocationWeather.WeatherHandlers.netatmo:
            self.handler = LocationWeather.WeatherHandlers.netatmo
            weather = NetAtmo().get_forecast_weather(location_id=self.id, days=self.days)
        else:
            raise ValueError("Unknown chanel")
        self.summary = weather["summary"]
        self.temp_min = weather["temp_min"]
        self.temp_max = weather["temp_max"]
        self.wind_speed = weather["wind_speed"]
        self.wind_degree = weather["wind_degree"]
        self.clouds_all = weather["clouds_all"]
        self.rain = weather["rain"]
        self.save()
