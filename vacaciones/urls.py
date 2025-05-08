from django.urls import path, include
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    SolicitudVacacionesListView,
    SolicitudVacacionesCreateView,
    SolicitudVacacionesUpdateView,
    SolicitudVacacionesDeleteView,
)

app_name = "vacaciones"

urlpatterns = [
    # -----------------------------------------
    # MODELO: PeriodoVacacional
    # -----------------------------------------
    path('periodos-vacacionales/', PeriodoVacacionalListView.as_view(), name="periodo_vacacional_list"),
    path('periodos-vacacionales/crear/', PeriodoVacacionalCreateView.as_view(), name="periodo_vacacional_create"),
    path('periodos-vacacionales/<int:pk>/editar/', PeriodoVacacionalUpdateView.as_view(), name="periodo_vacacional_update"),
    path('periodos-vacacionales/<int:pk>/eliminar/', PeriodoVacacionalDeleteView.as_view(), name="periodo_vacacional_delete"),

    # -----------------------------------------
    # MODELO: SolicitudVacaciones
    # -----------------------------------------
    path('solicitudes-vacaciones/', SolicitudVacacionesListView.as_view(), name="solicitud_vacaciones_list"),
    path('solicitudes-vacaciones/crear/', SolicitudVacacionesCreateView.as_view(), name="solicitud_vacaciones_create"),
    path('solicitudes-vacaciones/<int:pk>/editar/', SolicitudVacacionesUpdateView.as_view(), name="solicitud_vacaciones_update"),
    path('solicitudes-vacaciones/<int:pk>/eliminar/', SolicitudVacacionesDeleteView.as_view(), name="solicitud_vacaciones_delete"),

    # Rutas API REST
    path('api/', include('vacaciones.urls_api')),
]
