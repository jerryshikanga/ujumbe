from django.contrib import admin
from .models import Location, CurrentLocationWeather

# Register your models here.
admin.site.register(Location)
admin.site.register(CurrentLocationWeather)
