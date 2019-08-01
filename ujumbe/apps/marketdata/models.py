from django.db import models
from django_extensions.db.models import TimeStampedModel

from ujumbe.apps.weather.models import Location


# Create your models here.
class Product(TimeStampedModel):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


class ProductPrice(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)
    measurement_unit = models.CharField(max_length=20, null=True, blank=True)
    low_price = models.FloatField(null=True, blank=True)
    high_price = models.FloatField(null=True, blank=True)
    currency_code = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return "{} {} {} at {}".format(self.product.name, self.quantity, self.measurement_unit, self.location.name)
