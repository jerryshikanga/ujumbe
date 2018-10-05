from django.urls import path
from ujumbe.apps.weather import views


app_name = "weather"

urlpatterns = [
    path("current/list/", views.ListCurrentWeatherView.as_view(), name="list_current_weather"),
    path("forecast/list/", views.ListCurrentWeatherView.as_view(), name="list_forecast_weather"),
]