from django.contrib import admin
from ujumbe.apps.weather.models import CurrentWeather, ForecastWeather, Location

# Register your models here.
admin.site.register(CurrentWeather)
admin.site.register(ForecastWeather)
admin.site.register(Location)
