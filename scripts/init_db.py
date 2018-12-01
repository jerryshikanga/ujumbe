def create_countries():
    from ujumbe.apps.weather.models import Country
    import pycountry
    for _ in pycountry.countries:
        Country.objects.get_or_create(
            alpha2=_.alpha_2,
            alpha3=_.alpha_3,
            name=_.name
        )
    return Country.objects.all()


def create_kenyan_counties():
    from ujumbe.apps.weather.models import Country, Location
    kenya, _ = Country.objects.get_or_create(name="Kenya", alpha2="KE", alpha3="KEN")
    kenyan_counties = [
        "Baringo",
        "Bomet",
        "Bungoma"
        "Busia",
        "Elgeyo Marakwet",
        "Embu",
        "Garissa",
        "Homa Bay",
        "Isiolo",
        "Kajiado",
        "Kakamega",
        "Kericho",
        "Kiambu",
        "Kilifi",
        "Kirinyaga",
        "Kisii",
        "Kisumu",
        "Kitui",
        "Kwale",
        "Laikipia",
        "Lamu",
        "Machakos",
        "Makueni",
        "Mandera",
        "Meru",
        "Migori",
        "Marsabit",
        "Mombasa",
        "Muranga",
        "Nairobi",
        "Nakuru",
        "Nandi",
        "Narok",
        "Nyamira",
        "Nyandarua",
        "Nyeri",
        "Samburu",
        "Siaya",
        "Taita Taveta",
        "Tana River",
        "Tharaka Nithi",
        "Trans Nzoia",
        "Turkana",
        "Uasin Gishu",
        "Vihiga ",
        "Wajir",
        "West Pokot",
    ]
    for county in kenyan_counties:
        Location.objects.get_or_create(
            name=county,
            country=kenya
        )
    return Location.objects.all()


def create_super_user_with_profile(username: str, password: str, email: str, first_name: str, last_name: str,
                                   telephone: str):
    from ujumbe.apps.profiles.models import Profile

    from django.contrib.auth.models import User  # TODO :Change this to get_user_model

    superuser, created = User.objects.get_or_create(
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
        is_superuser=True,
        is_active=True,
        username=username,
    )
    superuser.set_password(password)
    superuser.save()
    profile, created = Profile.objects.get_or_create(
        user=superuser,
        telephone=telephone
    )
    return profile


def create_celery_beat_tasks():
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    # executes every 10 seconds.
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS
    )
    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name="Check and send subscriptions",
        task="ujumbe.apps.profiles.tasks.check_and_send_user_subscriptions"
    )


def run():
    create_countries()
    # create_kenyan_counties()
    create_super_user_with_profile(username="admin", password="password", email="jerryshikanga@gmail.com",
                                   first_name="Jerry", last_name="Shikanga", telephone="+254727447101")
    create_celery_beat_tasks()
