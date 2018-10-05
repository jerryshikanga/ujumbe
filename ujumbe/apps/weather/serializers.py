from ujumbe.apps.weather.models import CurrentWeather, ForecastWeather
from rest_framework import serializers

weather_model_fields = (
    "location", "summary", "temperature", "pressure", "humidity", "temp_min", "temp_max", "visibility", "wind_speed",
    "wind_degree", "clouds_all")


class CurrentWeatherSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = CurrentWeather
        fields = weather_model_fields
        read_only_fields = weather_model_fields


class ForecastWeatherSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = ForecastWeather
        fields = weather_model_fields + ("period",)
        read_only_fields = weather_model_fields