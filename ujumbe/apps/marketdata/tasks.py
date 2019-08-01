import logging

from celery import task

from ujumbe.apps.marketdata.handlers.mfarm import Mfarm
from ujumbe.apps.marketdata.models import Product, ProductPrice
from ujumbe.apps.weather.models import Location
from ujumbe.apps.profiles.models import Profile
from ujumbe.apps.messaging.models import OutgoingMessages

logger = logging.getLogger(__name__)


@task(bind=True, default_retry_delay=2 * 60 * 60, max_retries=3, acks_late=True)  # retry after two hours, for a max of two times
def get_product_prices(self):
    data = Mfarm().get_general_data()
    for product_dict in data:
        product, created = Product.objects.get_or_create(name=product_dict["product_name"])
        location = Location.try_resolve_location_by_name(product_dict["location_name"], "+254712345678")
        product_price, created = ProductPrice.objects.get_or_create(product=product, location=location)
        product_price.quantity = product_dict["quantity"]
        product_price.measurement_unit = product_dict["measurement_unit"]
        product_price.low_price = product_dict["low_price"]
        product_price.high_price = product_dict["high_price"]
        product_price.currency_code = product_dict["currency_code"]
        product_price.save()
    return data


@task
def send_user_product_price_today(product_name, phonenumber, location_name=None):
    product_queryset = Product.objects.filter(name__icontains=product_name)
    if not product_queryset.exists():
        text = "Details for product {} are not yet available.".format(product_name)
        OutgoingMessages.objects.create(text=text, phonenumber=phonenumber)
        return
    profile = Profile.resolve_profile_from_phonenumber(phonenumber)
    location = Location.try_resolve_location_by_name(location_name, phonenumber)
    if location is None:
        location = profile.location
    if location is None:
        text = "We could not determine a location. Please set a default one on your profile or provide in the request"
        OutgoingMessages.objects.create(text=text, phonenumber=phonenumber)
        return
    locations = []
    for l in Location.objects.all():
        locations.append({"location_id": l.id, "lat_long": (l.latitude, l.longitude)})
    current_coordinates = (location.latitude, location.longitude)
    min_distance, nearest_location = Location.calculate_nearest(current_coordinates, locations)
    product = product_queryset.first()
    product_price = ProductPrice.objects.get(product=product, location=nearest_location)
    text = "Price for Product {} is {} - {} {} for {} {} at Location {} which is {} kilometers away from {}.".format(
        product.name, product_price.low_price, product_price.high_price, product_price.currency_code,
        product_price.quantity, product_price.measurement_unit, location.name, min_distance, location_name
    )
    OutgoingMessages.objects.create(text=text, phonenumber=phonenumber)
    return
