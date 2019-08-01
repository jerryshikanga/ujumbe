from django.shortcuts import render


def home(request, *args, **kwargs):
    division_by_zero = 1 / 0
    return render(request, "home.html")
