from django.urls import path, include
from . import views, views_acciones as va
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    SolicitudVacacionesListView,
    SolicitudVacacionesCreateView,
    SolicitudVacacionesUpdateView,
    SolicitudVacacionesDeleteView,
    SolicitudVacacionesPDFView,
)

app_name = "vacaciones"

urlpatterns = [
    path("semaforo-cell/<int:pk>/", views.semaforo_cell, name="semaforo_cell"),

    ################# ELIMINAR SI NO SE USA #################
    path("<int:pk>/aprobar/", views.aprobar_view, name="aprobar_etapa"),
    path("<int:pk>/devolver/", views.devolver_view, name="devolver_etapa"),
    path("<int:pk>/autorizar/", views.autorizar_view, name="autorizar_rrhh"),
    path("<int:pk>/rechazar/", views.rechazar_view, name="rechazar_rrhh"),
    path("<int:pk>/reenviar/", views.reenviar_view, name="reenviar_funcionario"),
    #########################################################

    # Flujo simple para Solicitudes
    path("solicitudes/<int:pk>/enviar/", va.enviar_solicitud, name="solicitud_enviar"),
    path("solicitudes/<int:pk>/aprobar/", va.aprobar_solicitud, name="solicitud_aprobar"),
    path("solicitudes/<int:pk>/devolver/", va.devolver_solicitud, name="solicitud_devolver"),
    path("solicitudes/<int:pk>/rechazar/", va.rechazar_solicitud, name="solicitud_rechazar"),

    # Flujo simple para Reintegros
    path("reintegros/<int:pk>/enviar/", va.enviar_reintegro, name="reintegro_enviar"),
    path("reintegros/<int:pk>/aprobar/", va.aprobar_reintegro, name="reintegro_aprobar"),
    path("reintegros/<int:pk>/devolver/", va.devolver_reintegro, name="reintegro_devolver"),
    path("reintegros/<int:pk>/rechazar/", va.rechazar_reintegro, name="reintegro_rechazar"),

    # -----------------------------------------
    # MODELO: PeriodoVacacional
    # -----------------------------------------
    path('periodos-vacacionales/', PeriodoVacacionalListView.as_view(), name="periodo-vacacional-list"),
    path('periodos-vacacionales/crear/', PeriodoVacacionalCreateView.as_view(), name="periodo_vacacional_create"),
    path('periodos-vacacionales/<int:pk>/editar/', PeriodoVacacionalUpdateView.as_view(), name="periodo_vacacional_update"),
    path('periodos-vacacionales/<int:pk>/eliminar/', PeriodoVacacionalDeleteView.as_view(), name="periodo_vacacional_delete"),

    # -----------------------------------------
    # MODELO: SolicitudVacaciones
    # -----------------------------------------
    path('solicitudes-vacaciones/', SolicitudVacacionesListView.as_view(), name="solicitud-vacaciones-list"),
    path('solicitudes-vacaciones/crear/', SolicitudVacacionesCreateView.as_view(), name="solicitud_vacaciones_create"),
    path('solicitudes-vacaciones/<int:pk>/editar/', SolicitudVacacionesUpdateView.as_view(), name="solicitud_vacaciones_update"),
    path('solicitudes-vacaciones/<int:pk>/eliminar/', SolicitudVacacionesDeleteView.as_view(), name="solicitud_vacaciones_delete"),
    path('solicitudes/<int:pk>/pdf/', SolicitudVacacionesPDFView.as_view(), name="solicitud_vacaciones_pdf"),

    # Rutas API REST
    path('api/', include('vacaciones.urls_api')),
]
