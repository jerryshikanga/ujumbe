from django.db import models
from author.decorators import with_author
from django_extensions.db.models import TimeStampedModel
from djchoices import ChoiceItem, DjangoChoices
from django.utils import timezone

# Create your models here.
@with_author
class Location(TimeStampedModel):
    class KenyanCounties(DjangoChoices):
        Mombasa = ChoiceItem("Mombasa")
        Isiolo = ChoiceItem("Isiolo")
        Muranga = ChoiceItem("Murang'a")
        Laikipi = ChoiceItem("Laikipia")
        Siaya = ChoiceItem("Siaya")
        Kwale = ChoiceItem("Kwale")
        Meru = ChoiceItem("Meru")
        Kiambu = ChoiceItem("Kiambu")
        Nakuru = ChoiceItem("Nakuru")
        Kisumu = ChoiceItem("Kisumu")
        Kilifi = ChoiceItem("Kilifi")
        TharakaNithi = ChoiceItem("Tharaka-Nithi")
        Turkana = ChoiceItem("Turkana")
        Narok = ChoiceItem("Narok")
        HomaBay = ChoiceItem("homa-Bay")
        TanaRiver = ChoiceItem("Tana-River")
        Embu = ChoiceItem("Embu")
        WestPokot = ChoiceItem("West-Pokot")
        Kajiado = ChoiceItem("Kajiado")
        Migori = ChoiceItem("Migori")
        Lamu = ChoiceItem("Lamu")
        Kitui = ChoiceItem("Kitui")
        Samburu = ChoiceItem("Samburu")
        Kericho = ChoiceItem("Kericho")
        Kisii = ChoiceItem("Kisii")
        TaitaTaveta = ChoiceItem("Taita-Taveta")
        Machakos = ChoiceItem("Machakos")
        TransNzoia = ChoiceItem("Trans-Nzoia")
        Bomet = ChoiceItem("Bomet")
        Nyamira = ChoiceItem("Nyamira")
        Garissa = ChoiceItem("Garissa")
        Makueni = ChoiceItem("Makueni")
        UasinGishu = ChoiceItem("UasinGishu")
        Kakamega = ChoiceItem("Kakamega")
        Nairobi = ChoiceItem("Nairobi")
        Wajir = ChoiceItem("Wajir")
        Nyandarua = ChoiceItem("Nyandarua")
        ElgeyoMarakwet = ChoiceItem("Elgeyo-Marakwet")
        Vihiga = ChoiceItem("Vihiga")
        Mandera = ChoiceItem("Mandera")
        Nyeri = ChoiceItem("Nyeri")
        Nandi = ChoiceItem("Nandi")
        Bungoma = ChoiceItem("Bungoma")
        Marsabit = ChoiceItem("Marsabit")
        Kirinyaga = ChoiceItem("Kirinyaga")
        Baringo = ChoiceItem("Baringo")
        Busia = ChoiceItem("Busia")

    latitude = models.FloatField(default=0, blank=False, null=False)
    longitude = models.FloatField(default=0, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False, choices=KenyanCounties.choices)

    def __str__(self):
        return "{} Latitude : {}, Longitude : {}".format(self.name, self.latitude, self.longitude)


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