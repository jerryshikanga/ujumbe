"""ujumbe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

if settings.URL_IS_SHARED:
    shared_url_prefix = str(settings.URL_PREFIX)
    urlpatterns = [
        path(shared_url_prefix+'admin/', admin.site.urls),
        path(shared_url_prefix+'africastalking/', include('ujumbe.apps.africastalking.urls')),
        path(shared_url_prefix+'profile/', include('ujumbe.apps.profiles.urls')),
        path(shared_url_prefix+'weather/', include('ujumbe.apps.weather.urls')),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('africastalking/', include('ujumbe.apps.africastalking.urls')),
        path('profile/', include('ujumbe.apps.profiles.urls')),
        path('weather/', include('ujumbe.apps.weather.urls')),
    ]
