from django.shortcuts import render
from django.http import HttpResponse


def index(request, context="", mapcode=""):
    return render(request, "index.html", {})