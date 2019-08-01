from django.contrib import admin
from .models import ProductPrice, Product

# Register your models here.
admin.site.register(Product)
admin.site.register(ProductPrice)
