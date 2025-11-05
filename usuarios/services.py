from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from vacaciones.models import SolicitudVacaciones, AprobacionEtapa, PeriodoVacacional
from notificaciones.models import Notificacion
from core.permissions import (
    es_secretaria,
    es_jefe_inmediato,
    es_coordinador_administrativo,
    es_rrhh
)

def obtener_datos_dashboard_funcionario(user):
    """
    Obtiene los datos del dashboard para un funcionario regular.
    """
    try:
        funcionario = user.funcionario
    except:
        return None
    
    estado_vacaciones = funcionario.estado_de_vacaciones()
    dias_disponibles = estado_vacaciones.get('dias_pendientes_totales', 0)
    
    ultimo_periodo = estado_vacaciones.get('ultimo_periodo')
    ultimo_periodo_disfrutado = None

    if ultimo_periodo and ultimo_periodo.get('fecha_inicio'):
        fecha_inicio = ultimo_periodo['fecha_inicio']
        if isinstance(fecha_inicio, str):
            from datetime import datetime
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        meses_es = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        mes_nombre = meses_es.get(fecha_inicio.month, '')
        ultimo_periodo_disfrutado = f"{mes_nombre} {fecha_inicio.year}"
    
    solicitudes_en_curso = SolicitudVacaciones.objects.filter(
        funcionario=funcionario,
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    estado_solicitud_en_curso = None

    if solicitudes_en_curso > 0:
        primera_solicitud = SolicitudVacaciones.objects.filter(
            funcionario=funcionario,
            estado_solicitud__in=['pendiente', 'en_revision']
        ).first()
        if primera_solicitud:
            etapa_activa = primera_solicitud.etapa_activa
            if etapa_activa:
                estado_solicitud_en_curso = etapa_activa.estado
            else:
                estado_solicitud_en_curso = primera_solicitud.estado_solicitud
    
    notificaciones = Notificacion.objects.filter(
        funcionario=funcionario
    ).order_by('-fecha_hora_envio')[:5]
    
    return {
        'dias_disponibles': dias_disponibles,
        'ultimo_periodo_disfrutado': ultimo_periodo_disfrutado,
        'solicitudes_en_curso': solicitudes_en_curso,
        'estado_solicitud_en_curso': estado_solicitud_en_curso,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_jefe(user):
    """
    Obtiene los datos del dashboard para un Jefe Inmediato.
    """
    try:
        jefe_func = user.funcionario
    except:
        return None
    
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        funcionario__jefe_inmediato=jefe_func,
        aprobaciones__etapa='JEFE',
        aprobaciones__estado='pendiente'
    ).distinct().count()
    
    solicitudes_totales = SolicitudVacaciones.objects.filter(
        funcionario__jefe_inmediato=jefe_func
    ).distinct().count()
    
    notificaciones = Notificacion.objects.filter(
        funcionario=jefe_func
    ).order_by('-fecha_hora_envio')[:5]
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_coordinador(user):
    """
    Obtiene los datos del dashboard para un Coordinador Administrativo.
    """
    try:
        coord_func = user.funcionario
    except:
        return None
    
    ids_jefe_aprobada = set(
        SolicitudVacaciones.objects.filter(
            funcionario__facultad_dependencia=coord_func.facultad_dependencia,
            aprobaciones__etapa='JEFE',
            aprobaciones__estado='aprobada'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_coord_pendiente = set(
        SolicitudVacaciones.objects.filter(
            funcionario__facultad_dependencia=coord_func.facultad_dependencia,
            aprobaciones__etapa='COORD',
            aprobaciones__estado='pendiente'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_pendientes = ids_jefe_aprobada & ids_coord_pendiente
    solicitudes_pendientes = len(ids_pendientes)
    
    solicitudes_totales = SolicitudVacaciones.objects.filter(
        funcionario__facultad_dependencia=coord_func.facultad_dependencia
    ).distinct().count()
    
    notificaciones = Notificacion.objects.filter(
        funcionario=coord_func
    ).order_by('-fecha_hora_envio')[:5]
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_secretaria(user):
    """
    Obtiene los datos del dashboard para una Secretaria.
    """
    try:
        secretaria_func = user.funcionario
    except:
        return None
    
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    solicitudes_totales = SolicitudVacaciones.objects.count()
    
    notificaciones = Notificacion.objects.filter(
        funcionario=secretaria_func
    ).order_by('-fecha_hora_envio')[:5]
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_rrhh(user):
    """
    Obtiene los datos del dashboard para Recursos Humanos.
    """
    try:
        rrhh_func = user.funcionario
    except:
        return None
    
    ids_jefe_aprobada = set(
        SolicitudVacaciones.objects.filter(
            aprobaciones__etapa='JEFE',
            aprobaciones__estado='aprobada'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_coord_aprobada = set(
        SolicitudVacaciones.objects.filter(
            aprobaciones__etapa='COORD',
            aprobaciones__estado='aprobada'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_jefe_y_coord = ids_jefe_aprobada & ids_coord_aprobada
    
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        id__in=ids_jefe_y_coord
    ).exclude(
        aprobaciones__etapa='RRHH',
        aprobaciones__estado__in=['autorizada', 'rechazada']
    ).distinct().count()
    
    solicitudes_totales = SolicitudVacaciones.objects.count()
    
    notificaciones = Notificacion.objects.filter(
        funcionario=rrhh_func
    ).order_by('-fecha_hora_envio')[:5]
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard(user):
    """
    Obtiene los datos del dashboard según el rol del usuario.
    """
    if es_rrhh(user):
        return obtener_datos_dashboard_rrhh(user)
    elif es_secretaria(user):
        return obtener_datos_dashboard_secretaria(user)
    elif es_coordinador_administrativo(user):
        return obtener_datos_dashboard_coordinador(user)
    elif es_jefe_inmediato(user):
        return obtener_datos_dashboard_jefe(user)
    else:
        return obtener_datos_dashboard_funcionario(user)
