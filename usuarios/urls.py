from django.urls import path
from .views import CustomLoginView, dashboard, custom_logout

app_name = "usuarios"

urlpatterns = [
    path("iniciar-sesion/", CustomLoginView.as_view(), name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("cerrar-sesion/", custom_logout, name="logout"),
]
