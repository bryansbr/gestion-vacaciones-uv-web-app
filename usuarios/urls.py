from django.urls import path
from .views import CustomLoginView

urlpatterns = [
    path("iniciar-sesion/", CustomLoginView.as_view(), name="login"),
]
