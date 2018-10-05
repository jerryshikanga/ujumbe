from rest_framework import permissions
from rest_framework.generics import ListAPIView
from ujumbe.apps.weather.serializers import CurrentWeatherSerializer, ForecastWeatherSerializer
from ujumbe.apps.weather.models import CurrentWeather, ForecastWeather


# Create your views here.
class ListCurrentWeatherView(ListAPIView):
    serializer_class = CurrentWeatherSerializer
    queryset = CurrentWeather.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]


class ListForecastWeatherView(ListAPIView):
    serializer_class = ForecastWeatherSerializer
    queryset = ForecastWeather.objects.valid()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]
