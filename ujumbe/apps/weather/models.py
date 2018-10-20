from author.decorators import with_author
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
import datetime


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
    lat_ne = models.FloatField(blank=True, null=True)
    lat_sw = models.FloatField(blank=True, null=True)
    lon_ne = models.FloatField(blank=True, null=True)
    lon_sw = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    owm_city_id = models.IntegerField(default=0, null=True, blank=True)
    owm_details_set = models.BooleanField(default=False, null=False, blank=False)

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

    @classmethod
    def try_resolve_location_by_name(cls, name: str, phonenumber: str):
        from phone_iso3166.country import phone_country
        country = Country.objects.filter(alpha2=phone_country(phonenumber)).first()
        return Location.objects.in_country(country).filter(name__icontains=name).first()


class LocationWeather(TimeStampedModel):
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

    def valid(self):
        raise NotImplementedError("The valid method should be implemented")

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

    def valid(self):
        return datetime.datetime.now() - datetime.timedelta(hours=3) <= self.modified

    @property
    def description(self):
        return "Current weather {}".format(super(CurrentWeather, self).description)

    @property
    def detailed(self):
        return "Current weather {}".format(super(CurrentWeather, self).detailed)


class ForecastWeather(LocationWeather):
    period = models.DurationField(null=False, blank=False)
    forecast_time = models.DateTimeField(null=False, blank=False, default=timezone.now)

    class Meta(object):
        verbose_name = "Forecast Weather"
        verbose_name_plural = "Forecast Weather"

    @property
    def description(self):
        return "Forecast for {}, {}".format(self.period, super(ForecastWeather, self).description)

    @property
    def detailed(self):
        return "Forecast for {}, {}".format(self.period, super(ForecastWeather, self).detailed)

    def valid(self):
        return datetime.datetime.now() <= (self.forecast_time + self.period)
