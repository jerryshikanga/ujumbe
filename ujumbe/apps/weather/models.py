from author.decorators import with_author
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel


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
    name = models.CharField(max_length=255, blank=False, null=False)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)

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
    def try_resolve_location_by_name(cls, name: str, phonenumber: str = None):
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
    visibility = models.IntegerField(default=0, null=False, blank=False)
    wind_speed = models.IntegerField(default=0, null=False, blank=False)
    wind_degree = models.IntegerField(default=0, null=False, blank=False)
    clouds_all = models.IntegerField(default=0, null=False, blank=False)

    class Meta(object):
        abstract = True
        verbose_name = "Weather"
        verbose_name_plural = "Weather"

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

    @property
    def description(self):
        return "Current weather {}".format(super(CurrentWeather, self).description)

    @property
    def detailed(self):
        return "Current weather {}".format(super(CurrentWeather, self).detailed)


class ForecastWeatherManager(models.Manager):
    def valid(self):
        queryset = super(ForecastWeatherManager, self).get_queryset()
        timenow = timezone.now()
        return_data = []
        for weather_item in queryset:
            if timenow <= (weather_item.created + weather_item.period):
                return_data.append(weather_item)
        return return_data

    def expired(self):
        queryset = super(ForecastWeatherManager, self).get_queryset()
        timenow = timezone.now()
        return_data = []
        for weather_item in queryset:
            if timenow > (weather_item.created + weather_item.period):
                return_data.append(weather_item)
        return return_data


class ForecastWeather(LocationWeather):
    period = models.DurationField(null=False, blank=False)

    objects = ForecastWeatherManager()

    class Meta(object):
        verbose_name = "Forecast Weather"
        verbose_name_plural = "Forecast Weather"

    @property
    def description(self):
        return "Forecast for {}, {}".format(self.period, super(ForecastWeather, self).description)

    @property
    def detailed(self):
        return "Forecast for {}, {}".format(self.period, super(ForecastWeather, self).detailed)
