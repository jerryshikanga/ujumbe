from django.db import models
from django_extensions.db.models import TimeStampedModel
from author.decorators import with_author


# Create your models here.
@with_author
class Location(TimeStampedModel):
    latitude = models.FloatField(default=0, blank=False, null=False)
    longitude = models.FloatField(default=0, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False, default="")


@with_author
class CurrentLocationWeather(TimeStampedModel):
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, null=False, blank=False, default="")
    temperature = models.IntegerField(default=0, null=False, blank=False)
    pressure = models.IntegerField(default=0, null=False, blank=False)
    humidity = models.IntegerField(default=0, null=False, blank=False)
    temp_min = models.IntegerField(default=0, null=False, blank=False)
    temp_max = models.IntegerField(default=0, null=False, blank=False)
    visibility = models.IntegerField(default=0, null=False, blank=False)
    wind_speed = models.IntegerField(default=0, null=False, blank=False)
    wind_degree = models.IntegerField(default=0, null=False, blank=False)
    clouds_all = models.IntegerField(default=0, null=False, blank=False)
