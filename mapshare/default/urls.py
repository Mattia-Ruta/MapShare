from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("getMapcodeAJAX", views.getMapcodeAJAX, name="mapcodeAJAX"),
    path("<str:mapcode>", views.index, name="index"),
    path("<str:context>/<str:mapcode>", views.index, name="index"),
]