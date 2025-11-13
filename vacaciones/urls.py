from django.urls import path, include

from . import views, views_jefe, views_coord, views_rrhh
from .views import (
    PeriodoVacacionalListView,
    PeriodoVacacionalCreateView,
    PeriodoVacacionalUpdateView,
    PeriodoVacacionalDeleteView,
    SecretariaSolicitudesListView,
    SecretariaSolicitudCreateView,
    SecretariaSolicitudUpdateView,
    SecretariaSolicitudDeleteView,
    SecretariaReintegrosListView,
    SecretariaReintegroCreateView,
    SecretariaReintegroUpdateView,
    SecretariaReintegroDeleteView,
    SolicitudVacacionesListView,
    SolicitudVacacionesCreateView,
    SolicitudVacacionesUpdateView,
    SolicitudVacacionesDeleteView,
    ReintegroVacacionesListView,
    ReintegroVacacionesCreateView,
    ReintegroVacacionesUpdateView,
    ReintegroVacacionesDeleteView,
    SolicitudVacacionesPDFView,
    ReintegroVacacionesPDFView
)

app_name = "vacaciones"

urlpatterns = [
    # --- Semáforo ---
    path("semaforo-cell/<int:pk>/", views.semaforo_cell, name="semaforo_cell"),
    path("semaforo-cell-reintegro/<int:pk>/", views.semaforo_cell_reintegro, name="semaforo_cell_reintegro"),

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
    # MODELO: ReintegroVacaciones (Funcionario)
    # -----------------------------------------
    path("reintegros-vacaciones/",                     ReintegroVacacionesListView.as_view(),   name="reintegro-vacaciones-list"),
    path("reintegros-vacaciones/crear/",               ReintegroVacacionesCreateView.as_view(), name="reintegro_vacaciones_create"),
    path("reintegros-vacaciones/<int:pk>/editar/",     ReintegroVacacionesUpdateView.as_view(), name="reintegro_vacaciones_update"),
    path("reintegros-vacaciones/<int:pk>/eliminar/",   ReintegroVacacionesDeleteView.as_view(), name="reintegro_vacaciones_delete"),

    # -----------------------------------------
    # Jefe Inmediato
    # -----------------------------------------
    path("jefe/solicitudes/",                         views_jefe.SolicitudesJefeListView.as_view(), name="jefe_solicitudes_list"),
    path("jefe/solicitudes/crear/",                   views_jefe.JefeSolicitudCreateView.as_view(), name="jefe-solicitud-create"),
    path("jefe/solicitudes/<int:pk>/aprobar/",        views_jefe.aprobar_solicitud,               name="jefe_aprobar_solicitud"),
    path("jefe/solicitudes/<int:pk>/devolver/",       views_jefe.devolver_solicitud,              name="jefe_devolver_solicitud"),
    path("jefe/solicitudes/<int:pk>/enviar-proximo/", views_jefe.enviar_solicitud_proximo_revisor, name="jefe_enviar_proximo_revisor"),

    # -----------------------------------------
    # Secretaria
    # -----------------------------------------
    path("secretaria/solicitudes/",                         SecretariaSolicitudesListView.as_view(),   name="secretaria-solicitudes-list"),
    path("secretaria/solicitudes/crear/",                   SecretariaSolicitudCreateView.as_view(),   name="secretaria-solicitud-create"),
    path("secretaria/solicitudes/<int:pk>/editar/",         SecretariaSolicitudUpdateView.as_view(),   name="secretaria-solicitud-update"),
    path("secretaria/solicitudes/<int:pk>/eliminar/",       SecretariaSolicitudDeleteView.as_view(),   name="secretaria-solicitud-delete"),
    path("secretaria/reintegros/",                          SecretariaReintegrosListView.as_view(),    name="secretaria-reintegros-list"),
    path("secretaria/reintegros/crear/",                    SecretariaReintegroCreateView.as_view(),    name="secretaria-reintegro-create"),
    path("secretaria/reintegros/<int:pk>/editar/",          SecretariaReintegroUpdateView.as_view(),    name="secretaria-reintegro-update"),
    path("secretaria/reintegros/<int:pk>/eliminar/",        SecretariaReintegroDeleteView.as_view(),   name="secretaria-reintegro-delete"),

    # -----------------------------------------
    # Coordinador Administrativo
    # -----------------------------------------
    path("coord/solicitudes/",                         views_coord.SolicitudesCoordListView.as_view(), name="coord_solicitudes_list"),
    path("coord/solicitudes/<int:pk>/aprobar/",        views_coord.aprobar_solicitud,               name="coord_aprobar_solicitud"),
    path("coord/solicitudes/<int:pk>/devolver/",       views_coord.devolver_solicitud,              name="coord_devolver_solicitud"),

    # -----------------------------------------
    # Recursos Humanos (RRHH)
    # -----------------------------------------
    path("rrhh/solicitudes/",                         views_rrhh.SolicitudesRRHHListView.as_view(), name="rrhh_solicitudes_list"),
    path("rrhh/solicitudes/<int:pk>/autorizar/",      views_rrhh.autorizar_solicitud,               name="rrhh_autorizar_solicitud"),
    path("rrhh/solicitudes/<int:pk>/rechazar/",       views_rrhh.rechazar_solicitud,                name="rrhh_rechazar_solicitud"),

    path("reintegros/<int:pk>/firmar/",    views.firmar_reintegro_view,    name="reintegro_firmar"),
    path("reintegros/<int:pk>/enviar/",    views.reenviar_reintegro_view,  name="reintegro_enviar"),
    path("reintegros/<int:pk>/aprobar/",   views.aprobar_reintegro_view,   name="reintegro_aprobar"),
    path("reintegros/<int:pk>/devolver/",  views.devolver_reintegro_view,  name="reintegro_devolver"),
    path("reintegros/<int:pk>/autorizar/", views.autorizar_reintegro_view, name="reintegro_autorizar"),
    path("reintegros/<int:pk>/rechazar/",  views.rechazar_reintegro_view,  name="reintegro_rechazar"),
    path("reintegros/<int:pk>/pdf/",       ReintegroVacacionesPDFView.as_view(), name="reintegro_laboral_p4_pdf"),
    
    # -----------------------------------------
    # API REST
    # -----------------------------------------
    path("api/", include("vacaciones.urls_api")),
]
