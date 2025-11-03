from django.urls import path, include

from . import views, views_jefe
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    SecretariaSolicitudesListView,
    SecretariaSolicitudCreateView,
    SecretariaSolicitudUpdateView,
    SecretariaSolicitudDeleteView,
    SolicitudVacacionesListView,
    SolicitudVacacionesCreateView,
    SolicitudVacacionesUpdateView,
    SolicitudVacacionesDeleteView,
    SolicitudVacacionesPDFView,
)

app_name = "vacaciones"

urlpatterns = [
    # --- Semáforo ---
    path("semaforo-cell/<int:pk>/", views.semaforo_cell, name="semaforo_cell"),

    # --- Acciones de flujo por etapa (Genéricas)
    path("<int:pk>/aprobar/",   views.aprobar_view,    name="aprobar_etapa"),
    path("<int:pk>/devolver/",  views.devolver_view,   name="devolver_etapa"),
    path("<int:pk>/autorizar/", views.autorizar_view,  name="autorizar_rrhh"),
    path("<int:pk>/rechazar/",  views.rechazar_view,   name="rechazar_rrhh"),
    path("<int:pk>/reenviar/",  views.reenviar_view,   name="reenviar_funcionario"),

    # -----------------------------------------
    # MODELO: PeriodoVacacional
    # -----------------------------------------
    path("periodos-vacacionales/",                   PeriodoVacacionalListView.as_view(),   name="periodo-vacacional-list"),
    path("periodos-vacacionales/crear/",             PeriodoVacacionalCreateView.as_view(), name="periodo_vacacional_create"),
    path("periodos-vacacionales/<int:pk>/editar/",   PeriodoVacacionalUpdateView.as_view(), name="periodo_vacacional_update"),
    path("periodos-vacacionales/<int:pk>/eliminar/", PeriodoVacacionalDeleteView.as_view(), name="periodo_vacacional_delete"),

    # -----------------------------------------
    # MODELO: SolicitudVacaciones (Funcionario)
    # -----------------------------------------
    path("solicitudes-vacaciones/",                     SolicitudVacacionesListView.as_view(),   name="solicitud-vacaciones-list"),
    path("solicitudes-vacaciones/crear/",               SolicitudVacacionesCreateView.as_view(), name="solicitud_vacaciones_create"),
    path("solicitudes-vacaciones/<int:pk>/editar/",     SolicitudVacacionesUpdateView.as_view(), name="solicitud_vacaciones_update"),
    path("solicitudes-vacaciones/<int:pk>/eliminar/",   SolicitudVacacionesDeleteView.as_view(), name="solicitud_vacaciones_delete"),
    path("solicitudes/<int:pk>/pdf/",                   SolicitudVacacionesPDFView.as_view(),    name="solicitud_vacaciones_pdf"),

    # -----------------------------------------
    # Jefe Inmediato
    # -----------------------------------------
    path("jefe/solicitudes/",                         views_jefe.SolicitudesJefeListView.as_view(), name="jefe_solicitudes_list"),
    path("jefe/solicitudes/crear/",                   views_jefe.JefeSolicitudCreateView.as_view(), name="jefe-solicitud-create"),
    path("jefe/solicitudes/<int:pk>/aprobar/",        views_jefe.aprobar_solicitud,               name="jefe_aprobar_solicitud"),
    path("jefe/solicitudes/<int:pk>/devolver/",       views_jefe.devolver_solicitud,              name="jefe_devolver_solicitud"),

    # -----------------------------------------
    # Secretaria
    # -----------------------------------------
    path("secretaria/solicitudes/",                         SecretariaSolicitudesListView.as_view(),   name="secretaria-solicitudes-list"),
    path("secretaria/solicitudes/crear/",                   SecretariaSolicitudCreateView.as_view(),   name="secretaria-solicitud-create"),
    path("secretaria/solicitudes/<int:pk>/editar/",         SecretariaSolicitudUpdateView.as_view(),   name="secretaria-solicitud-update"),
    path("secretaria/solicitudes/<int:pk>/eliminar/",       SecretariaSolicitudDeleteView.as_view(),   name="secretaria-solicitud-delete"),

    # --- API REST
    path("api/", include("vacaciones.urls_api")),
]
