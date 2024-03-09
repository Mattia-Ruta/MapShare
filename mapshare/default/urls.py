from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("getMapcodeAJAX", views.getMapcodeAJAX, name="mapcodeAJAX"),
    path("favicon.ico", views.favicon, name="favicon"),
    path("about", views.about, name="about"),
    path("<str:mapcode>", views.index, name="index"),
    path("<str:context>/<str:mapcode>", views.index, name="index"),
]