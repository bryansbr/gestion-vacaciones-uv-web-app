from django.urls import path, include
from . import views, views_jefe, views_coord, views_rrhh, views_reportes, views_estado
from .views import *


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
    path("jefe/reintegros/",                          views_jefe.ReintegrosJefeListView.as_view(), name="jefe_reintegros_list"),
    path("jefe/reintegros/crear/",                    views_jefe.JefeReintegroCreateView.as_view(), name="jefe-reintegro-create"),
    path("jefe/reintegros/<int:pk>/aprobar/",         views_jefe.aprobar_reintegro,                name="jefe_aprobar_reintegro"),
    path("jefe/reintegros/<int:pk>/devolver/",        views_jefe.devolver_reintegro,               name="jefe_devolver_reintegro"),

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
    path("coord/reintegros/",                          views_coord.ReintegrosCoordListView.as_view(), name="coord_reintegros_list"),
    path("coord/reintegros/crear/",                    views_coord.CoordReintegroCreateView.as_view(), name="coord-reintegro-create"),
    path("coord/reintegros/<int:pk>/editar/",          views_coord.CoordReintegroUpdateView.as_view(), name="coord-reintegro-update"),
    path("coord/reintegros/<int:pk>/eliminar/",        views_coord.CoordReintegroDeleteView.as_view(), name="coord-reintegro-delete"),
    path("coord/reintegros/<int:pk>/aprobar/",         views_coord.aprobar_reintegro,                name="coord_aprobar_reintegro"),
    path("coord/reintegros/<int:pk>/devolver/",        views_coord.devolver_reintegro,               name="coord_devolver_reintegro"),

    # -----------------------------------------
    # Recursos Humanos (RRHH)
    # -----------------------------------------
    path("rrhh/solicitudes/",                         views_rrhh.SolicitudesRRHHListView.as_view(), name="rrhh_solicitudes_list"),
    path("rrhh/solicitudes/<int:pk>/autorizar/",      views_rrhh.autorizar_solicitud,               name="rrhh_autorizar_solicitud"),
    path("rrhh/solicitudes/<int:pk>/rechazar/",       views_rrhh.rechazar_solicitud,                name="rrhh_rechazar_solicitud"),
    path("rrhh/reintegros/",                          views_rrhh.ReintegrosRRHHListView.as_view(), name="rrhh_reintegros_list"),
    path("rrhh/reintegros/<int:pk>/autorizar/",       views_rrhh.autorizar_reintegro,               name="rrhh_autorizar_reintegro"),
    path("rrhh/reintegros/<int:pk>/rechazar/",        views_rrhh.rechazar_reintegro,                name="rrhh_rechazar_reintegro"),

    path("reintegros/<int:pk>/firmar/",    views.firmar_reintegro_view,    name="reintegro_firmar"),
    path("reintegros/<int:pk>/enviar/",    views.reenviar_reintegro_view,  name="reintegro_enviar"),
    path("reintegros/<int:pk>/aprobar/",   views.aprobar_reintegro_view,   name="reintegro_aprobar"),
    path("reintegros/<int:pk>/devolver/",  views.devolver_reintegro_view,  name="reintegro_devolver"),
    path("reintegros/<int:pk>/autorizar/", views.autorizar_reintegro_view, name="reintegro_autorizar"),
    path("reintegros/<int:pk>/rechazar/",  views.rechazar_reintegro_view,  name="reintegro_rechazar"),
    path("reintegros/<int:pk>/pdf/",       ReintegroVacacionesPDFView.as_view(), name="reintegro_laboral_p4_pdf"),
    
    # -----------------------------------------
    # REPORTES
    # -----------------------------------------
    path("reportes/", views_reportes.ReportesDashboardView.as_view(), name="reportes_dashboard"),
    path("reportes/exportar-solicitudes-csv/", views_reportes.ExportarSolicitudesCSVView.as_view(), name="exportar_solicitudes_csv"),
    path("reportes/exportar-reintegros-csv/", views_reportes.ExportarReintegrosCSVView.as_view(), name="exportar_reintegros_csv"),
    path("reportes/exportar-reporte-solicitudes/", views_reportes.ExportarReporteSolicitudesView.as_view(), name="exportar_reporte_solicitudes"),
    path("reportes/exportar-reporte-reintegros/", views_reportes.ExportarReporteReintegrosView.as_view(), name="exportar_reporte_reintegros"),
    path("reportes/exportar-estadisticas-solicitudes-csv/", views_reportes.ExportarEstadisticasSolicitudesCSVView.as_view(), name="exportar_estadisticas_solicitudes_csv"),
    path("reportes/exportar-estadisticas-reintegros-csv/", views_reportes.ExportarEstadisticasReintegrosCSVView.as_view(), name="exportar_estadisticas_reintegros_csv"),
    
    # -----------------------------------------
    # ESTADO DE VACACIONES
    # -----------------------------------------
    path("estado-vacaciones/", views_estado.EstadoVacacionesView.as_view(), name="estado_vacaciones"),
    
    # -----------------------------------------
    # API REST
    # -----------------------------------------
    path("api/", include("vacaciones.urls_api")),
]
