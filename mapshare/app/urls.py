from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
    path('contact/', views.contact, name='contact'),
]
