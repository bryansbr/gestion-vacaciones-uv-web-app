"""
Vistas para el módulo de reportes de vacaciones.
Proporciona dashboards y visualizaciones de estadísticas según el rol del usuario.
"""
from django.views.generic import TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.http import HttpResponse

import json
import csv
import logging

from datetime import date, datetime, timedelta
from typing import Optional

from vacaciones.services.reportes import obtener_reporte_completo, _filtrar_por_rol
from vacaciones.models import SolicitudVacaciones, ReintegroVacaciones
from core.models import FacultadDependencia
from core.permissions import (
    es_jefe_inmediato,
    es_secretaria,
    es_coordinador_administrativo,
    es_rrhh
)

class ReportesDashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del dashboard de reportes.
    
    Acceso permitido:
    - Jefe Inmediato: solo información de funcionarios a su cargo
    - Secretaria: solo funcionarios bajo su jefe inmediato
    - Coordinación Administrativa: solo su Facultad/Dependencia
    - RRHH: todos los funcionarios
    """
    template_name = 'vacaciones/reportes/dashboard-reportes.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga permisos para ver reportes."""
        user = request.user
        
        tiene_permiso = (
            es_jefe_inmediato(user) or
            es_secretaria(user) or
            es_coordinador_administrativo(user) or
            es_rrhh(user) or
            user.is_superuser
        )
        
        if not tiene_permiso:
            raise PermissionDenied("No tiene permisos para acceder a los reportes.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def _parsear_fecha(self, fecha_str: Optional[str]) -> Optional[date]:
        """Convierte string de fecha a objeto date."""
        if not fecha_str:
            return None
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        fecha_inicio_str = self.request.GET.get('fecha_inicio')
        fecha_fin_str = self.request.GET.get('fecha_fin')
        facultad_id_str = self.request.GET.get('facultad')
        
        fecha_inicio = self._parsear_fecha(fecha_inicio_str)
        fecha_fin = self._parsear_fecha(fecha_fin_str)
        
        if not fecha_inicio and not fecha_fin:
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=365)
        
        facultad_id = None
        if facultad_id_str:
            try:
                facultad_id = int(facultad_id_str)
            except (ValueError, TypeError):
                facultad_id = None
        
        if facultad_id and not (es_rrhh(user) or user.is_superuser):
            facultad_id = None
        
        logger = logging.getLogger(__name__)
        
        try:
            reporte = obtener_reporte_completo(
                user=user,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                facultad_id=facultad_id
            )
            logger.info(f"Reporte generado exitosamente para usuario {user.username}")
            logger.debug(f"Datos del reporte: {reporte}")
        except Exception as e:
            logger.error(f"Error al generar reporte para usuario {user.username}: {str(e)}", exc_info=True)
            reporte = {
                'estadisticas_solicitudes': {
                    'solicitudes_aprobadas': 0,
                    'solicitudes_devueltas': 0,
                    'solicitudes_autorizadas': 0,
                    'solicitudes_rechazadas': 0,
                    'solicitudes_pendientes': 0,
                    'solicitudes_totales': 0,
                },
                'solicitudes_por_facultad': [],
                'solicitudes_por_anio': [],
                'funcionarios_en_vacaciones': [],
                'reintegros_anticipados': {
                    'total_reintegros_anticipados': 0,
                    'por_estado': {},
                    'detalle': []
                },
            }
        
        facultades = []
        if es_rrhh(user) or user.is_superuser:
            facultades = FacultadDependencia.objects.all().order_by('nombre')
        
        rol_usuario = None

        if es_rrhh(user):
            rol_usuario = 'RRHH'
        elif es_coordinador_administrativo(user):
            rol_usuario = 'Coordinación Administrativa'
        elif es_jefe_inmediato(user):
            rol_usuario = 'Jefe Inmediato'
        elif es_secretaria(user):
            rol_usuario = 'Secretaria'
        
        estadisticas = reporte.get('estadisticas_solicitudes', {})
        datos_estados_json = json.dumps({
            'aprobadas': estadisticas.get('solicitudes_aprobadas', 0),
            'autorizadas': estadisticas.get('solicitudes_autorizadas', 0),
            'pendientes': estadisticas.get('solicitudes_pendientes', 0),
            'rechazadas': estadisticas.get('solicitudes_rechazadas', 0),
            'devueltas': estadisticas.get('solicitudes_devueltas', 0),
        })
        solicitudes_por_anio_json = json.dumps(reporte.get('solicitudes_por_anio', []))
        solicitudes_por_facultad_json = json.dumps(reporte.get('solicitudes_por_facultad', []))
        reintegros_por_estado_json = json.dumps(reporte.get('reintegros_anticipados', {}).get('por_estado', {}))
        
        context.update({
            'reporte': reporte,
            'facultades': facultades,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'fecha_inicio_str': fecha_inicio_str or (fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else ''),
            'fecha_fin_str': fecha_fin_str or (fecha_fin.strftime('%Y-%m-%d') if fecha_fin else ''),
            'facultad_seleccionada': facultad_id,
            'rol_usuario': rol_usuario,
            'puede_filtrar_facultad': es_rrhh(user) or user.is_superuser,
            'datos_estados_json': mark_safe(datos_estados_json),
            'solicitudes_por_anio_json': mark_safe(solicitudes_por_anio_json),
            'solicitudes_por_facultad_json': mark_safe(solicitudes_por_facultad_json),
            'reintegros_por_estado_json': mark_safe(reintegros_por_estado_json),
        })
        
        return context

class ExportarSolicitudesCSVView(LoginRequiredMixin, View):
    """
    Vista para exportar solicitudes de vacaciones a CSV.
    Respeta las restricciones por rol del usuario.
    """
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga permisos para exportar reportes."""
        user = request.user
        
        tiene_permiso = (
            es_jefe_inmediato(user) or
            es_secretaria(user) or
            es_coordinador_administrativo(user) or
            es_rrhh(user) or
            user.is_superuser
        )
        
        if not tiene_permiso:
            raise PermissionDenied("No tiene permisos para exportar reportes.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def _parsear_fecha(self, fecha_str: Optional[str]) -> Optional[date]:
        """Convierte string de fecha a objeto date."""
        if not fecha_str:
            return None
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    def get(self, request, *args, **kwargs):
        """Genera y retorna el archivo CSV con las solicitudes."""
        user = request.user
        
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        facultad_id_str = request.GET.get('facultad')
        
        fecha_inicio = self._parsear_fecha(fecha_inicio_str)
        fecha_fin = self._parsear_fecha(fecha_fin_str)
        
        facultad_id = None
        if facultad_id_str:
            try:
                facultad_id = int(facultad_id_str)
            except (ValueError, TypeError):
                facultad_id = None
        
        if facultad_id and not (es_rrhh(user) or user.is_superuser):
            facultad_id = None
        
        queryset = SolicitudVacaciones.objects.select_related(
            'funcionario',
            'funcionario__facultad_dependencia',
            'funcionario__estamento',
            'periodo_vacacional',
            'creada_por'
        )
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
        if facultad_id:
            queryset = queryset.filter(funcionario__facultad_dependencia_id=facultad_id)
        
        queryset, _ = _filtrar_por_rol(queryset, ReintegroVacaciones.objects.none(), user)
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_solicitudes_{date.today().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        
        encabezados = [
            'Código SABS',
            'Fecha Solicitud',
            'Funcionario',
            'Número Identificación',
            'Facultad/Dependencia',
            'Estamento',
            'Estado',
            'Fecha Inicio Vacaciones',
            'Fecha Fin Vacaciones',
            'Total Días Solicitados',
            'Fecha Pago',
            'Tiene Días Pendientes',
            'Es por Reintegro Anticipado',
            'Observaciones',
            'Creada Por',
            'Periodo Vacacional'
        ]
        writer.writerow(encabezados)
        
        for solicitud in queryset.order_by('-fecha_solicitud'):
            funcionario = solicitud.funcionario
            creada_por = solicitud.creada_por
            creada_por_nombre = ''
            if creada_por:
                if hasattr(creada_por, 'funcionario') and creada_por.funcionario:
                    creada_por_nombre = f"{creada_por.funcionario.nombre} {creada_por.funcionario.apellido}"
                else:
                    creada_por_nombre = creada_por.get_full_name() or creada_por.email or ''
            
            estado_display = dict(solicitud.ESTADOS).get(solicitud.estado_solicitud, solicitud.estado_solicitud)
            
            fila = [
                solicitud.codigo_sabs,
                solicitud.fecha_solicitud.strftime('%Y-%m-%d') if solicitud.fecha_solicitud else '',
                f"{funcionario.nombre} {funcionario.apellido}",
                funcionario.numero_identificacion,
                funcionario.facultad_dependencia.nombre if funcionario.facultad_dependencia else '',
                funcionario.estamento.nombre if funcionario.estamento else '',
                estado_display,
                solicitud.fecha_inicio_vacaciones.strftime('%Y-%m-%d') if solicitud.fecha_inicio_vacaciones else '',
                solicitud.fecha_fin_vacaciones.strftime('%Y-%m-%d') if solicitud.fecha_fin_vacaciones else '',
                solicitud.total_dias_solicitados,
                solicitud.fecha_pago.strftime('%Y-%m-%d') if solicitud.fecha_pago else '',
                'Sí' if solicitud.tiene_dias_pendientes else 'No',
                'Sí' if solicitud.es_por_reintegro_anticipado else 'No',
                solicitud.observaciones or '',
                creada_por_nombre,
                f"{solicitud.periodo_vacacional.fecha_inicio_periodo.year}" if solicitud.periodo_vacacional else '',
            ]
            writer.writerow(fila)
        
        return response

class ExportarReintegrosCSVView(LoginRequiredMixin, View):
    """
    Vista para exportar reintegros de vacaciones a CSV.
    Respeta las restricciones por rol del usuario.
    """
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga permisos para exportar reportes."""
        user = request.user
        
        tiene_permiso = (
            es_jefe_inmediato(user) or
            es_secretaria(user) or
            es_coordinador_administrativo(user) or
            es_rrhh(user) or
            user.is_superuser
        )
        
        if not tiene_permiso:
            raise PermissionDenied("No tiene permisos para exportar reportes.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def _parsear_fecha(self, fecha_str: Optional[str]) -> Optional[date]:
        """Convierte string de fecha a objeto date."""
        if not fecha_str:
            return None
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    def get(self, request, *args, **kwargs):
        """Genera y retorna el archivo CSV con los reintegros."""
        user = request.user
        
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        facultad_id_str = request.GET.get('facultad')
        
        fecha_inicio = self._parsear_fecha(fecha_inicio_str)
        fecha_fin = self._parsear_fecha(fecha_fin_str)
        
        facultad_id = None
        if facultad_id_str:
            try:
                facultad_id = int(facultad_id_str)
            except (ValueError, TypeError):
                facultad_id = None
        
        if facultad_id and not (es_rrhh(user) or user.is_superuser):
            facultad_id = None
        
        queryset = ReintegroVacaciones.objects.select_related(
            'funcionario',
            'funcionario__facultad_dependencia',
            'funcionario__estamento',
            'periodo_vacacional',
            'solicitud_vacaciones',
            'creada_por'
        )
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
        if facultad_id:
            queryset = queryset.filter(funcionario__facultad_dependencia_id=facultad_id)
        
        _, queryset = _filtrar_por_rol(SolicitudVacaciones.objects.none(), queryset, user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_reintegros_{date.today().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        
        encabezados = [
            'Código SABS',
            'Fecha Solicitud',
            'Fecha Reintegro',
            'Funcionario',
            'Número Identificación',
            'Facultad/Dependencia',
            'Estamento',
            'Estado',
            'Motivo Reintegro',
            'Es Reintegro Anticipado',
            'Fecha Disfrute Desde',
            'Fecha Disfrute Hasta',
            'Días Disfrutados',
            'Días Pendientes',
            'Tipo Días Pendientes',
            'Días Disfrutados Hábiles',
            'Días Disfrutados Calendario',
            'Días Pendientes Hábiles',
            'Días Pendientes Calendario',
            'Código Solicitud Asociada',
            'Observaciones',
            'Creado Por',
            'Periodo Vacacional'
        ]
        writer.writerow(encabezados)
        
        for reintegro in queryset.order_by('-fecha_solicitud'):
            funcionario = reintegro.funcionario
            creada_por = reintegro.creada_por
            creada_por_nombre = ''
            if creada_por:
                if hasattr(creada_por, 'funcionario') and creada_por.funcionario:
                    creada_por_nombre = f"{creada_por.funcionario.nombre} {creada_por.funcionario.apellido}"
                else:
                    creada_por_nombre = creada_por.get_full_name() or creada_por.email or ''

            estado_display = dict(reintegro.ESTADOS).get(reintegro.estado_solicitud, reintegro.estado_solicitud)
            motivo_display = dict(reintegro.MOTIVOS_REINTEGRO).get(reintegro.motivo_reintegro, reintegro.motivo_reintegro)
            tipo_dias_display = dict(reintegro.TIPO_DIAS).get(reintegro.tipo_dias_pendientes, reintegro.tipo_dias_pendientes)
            
            fila = [
                reintegro.codigo_sabs,
                reintegro.fecha_solicitud.strftime('%Y-%m-%d') if reintegro.fecha_solicitud else '',
                reintegro.fecha_reintegro.strftime('%Y-%m-%d') if reintegro.fecha_reintegro else '',
                f"{funcionario.nombre} {funcionario.apellido}",
                funcionario.numero_identificacion,
                funcionario.facultad_dependencia.nombre if funcionario.facultad_dependencia else '',
                funcionario.estamento.nombre if funcionario.estamento else '',
                estado_display,
                motivo_display,
                'Sí' if reintegro.es_reintegro_anticipado else 'No',
                reintegro.fecha_disfrute_desde.strftime('%Y-%m-%d') if reintegro.fecha_disfrute_desde else '',
                reintegro.fecha_disfrute_hasta.strftime('%Y-%m-%d') if reintegro.fecha_disfrute_hasta else '',
                reintegro.dias_disfrutados,
                reintegro.dias_pendientes,
                tipo_dias_display,
                reintegro.dias_disfrutados_habiles,
                reintegro.dias_disfrutados_calendario,
                reintegro.dias_pendientes_habiles,
                reintegro.dias_pendientes_calendario,
                reintegro.solicitud_vacaciones.codigo_sabs if reintegro.solicitud_vacaciones else '',
                reintegro.observaciones or '',
                creada_por_nombre,
                f"{reintegro.periodo_vacacional.fecha_inicio_periodo.year}" if reintegro.periodo_vacacional else '',
            ]
            writer.writerow(fila)
        
        return response
