from django.urls import path
from .views import CustomLoginView, dashboard, custom_logout
from .views_api import EstadoVacacionesView

app_name = "usuarios"

urlpatterns = [
    path("iniciar-sesion/", CustomLoginView.as_view(), name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("cerrar-sesion/", custom_logout, name="logout"),
    path("api/estado-vacaciones/", EstadoVacacionesView.as_view(), name="estado_vacaciones"),
]
