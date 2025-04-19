from django.urls import path
from .views import home

urlpatterns = [
    path("usuarios/dashboard/", home, name="home"),
]
