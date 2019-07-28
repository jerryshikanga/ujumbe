from ujumbe.apps.profiles.models import Profile, AccountCharges, Subscription
from ujumbe.apps.weather.models import Location, Country, CurrentWeather, ForecastWeather
from ujumbe.apps.messaging.models import IncomingMessage, OutgoingMessages
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django.contrib.auth import get_user_model

User = get_user_model()


def delete_tables_individual():
    Subscription.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.all().delete()
    AccountCharges.objects.all().delete()

    ForecastWeather.objects.all().delete()
    CurrentWeather.objects.all().delete()
    Location.objects.all().delete()
    Country.objects.all().delete()

    IncomingMessage.objects.all().delete()
    OutgoingMessages.objects.all().delete()

    IntervalSchedule.objects.all().delete()
    PeriodicTask.objects.all().delete()


def delete_and_create_db():
    import MySQLdb as sql
    from django.conf import settings
    db_settings = settings.DATABASES["default"]
    db = sql.connect(host="localhost", user=db_settings["USER"], password=db_settings["PASSWORD"], db=db_settings["NAME"])
    cursor = db.cursor()
    query = "DROP DATABASE {}; ".format(db_settings["NAME"])
    cursor.execute(query)
    query = "CREATE DATABASE {}; ".format(db_settings["NAME"])
    cursor.execute(query)
    db.close()


def run():
    # delete_tables_individual()
    delete_and_create_db()
