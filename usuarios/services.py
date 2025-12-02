from django.utils import timezone
from types import SimpleNamespace

from vacaciones.models import (
    HistoricoAcciones, 
    PeriodoVacacional, 
    SolicitudVacaciones, 
    ReintegroVacaciones
)
from vacaciones.services.estado_vacaciones import (
    _calcular_dias_habiles_calendario_solicitud,
    _obtener_tipo_dias_periodo,
    obtener_tipo_calculo_dias,
    obtener_ultimo_periodo_disfrutado,
)
from notificaciones.models import Notificacion
from core.permissions import (
    es_secretaria,
    es_jefe_inmediato,
    es_coordinador_administrativo,
    es_rrhh
)
from usuarios.models import Funcionario

# ==========================================================
# CONSTANTES
# ==========================================================
ESTADOS_NOVEDADES_INTERES = {'aprobada', 'autorizada', 'devuelta', 'rechazada'}

def _actor_desde_historial(historial):
    actor = (historial.grupo_autorizador or '').strip()
    if actor:
        return actor
    funcionario_actor = getattr(historial.usuario, 'funcionario', None)
    if funcionario_actor:
        nombre = f"{funcionario_actor.nombre} {funcionario_actor.apellido}".strip()
        if nombre:
            return nombre
    return historial.usuario.get_full_name() or historial.usuario.email

def _formatear_novedad_historial(historial):
    solicitud = historial.solicitud_vacaciones
    if not solicitud or historial.nuevo_estado is None:
        return None

    estado = historial.nuevo_estado.lower()
    if estado not in ESTADOS_NOVEDADES_INTERES:
        return None

    funcionario = solicitud.funcionario
    nombre_funcionario = f"{funcionario.nombre} {funcionario.apellido}".strip()
    actor = _actor_desde_historial(historial)

    estado_texto = {
        'aprobada': 'aprobada',
        'autorizada': 'autorizada',
        'devuelta': 'devuelta',
        'rechazada': 'rechazada',
    }.get(estado, historial.get_accion_realizada_display().lower())

    mensaje = f"La solicitud {solicitud.codigo_sabs} de {nombre_funcionario} fue {estado_texto}"
    if actor:
        mensaje += f" por {actor}"

    observacion = (historial.observacion or '').strip()
    if observacion:
        if estado == 'rechazada':
            mensaje += f". Motivo del rechazo: {observacion}"
        else:
            mensaje += f". Observación: {observacion}"

    return SimpleNamespace(
        asunto=f"Novedad solicitud {solicitud.codigo_sabs}",
        mensaje=mensaje,
        fecha_hora_envio=historial.fecha_hora_accion,
    )

def _combinar_notificaciones(base_queryset, extras, limite=5):
    elementos = list(base_queryset)
    elementos.extend([extra for extra in extras if extra is not None])
    elementos.sort(key=lambda item: getattr(item, 'fecha_hora_envio', timezone.now()), reverse=True)
    return elementos[:limite]

def obtener_ultimo_periodo_disfrutado_formateado(funcionario: Funcionario):
    """
    Obtiene el último periodo disfrutado formateado para mostrar en el dashboard.
    
    Returns:
        str con los años del periodo (ej: "2021 - 2022") o None
    """
    if not funcionario:
        return None
    
    ultimo_periodo_disfrutado_info = obtener_ultimo_periodo_disfrutado(funcionario)
    
    if ultimo_periodo_disfrutado_info:
        fecha_inicio = ultimo_periodo_disfrutado_info['fecha_inicio']
        fecha_fin = ultimo_periodo_disfrutado_info['fecha_fin']
        año_inicio = fecha_inicio.year
        año_fin = fecha_fin.year
        
        if año_inicio == año_fin:
            return str(año_inicio)
        else:
            return f"{año_inicio} - {año_fin}"
    
    return None

def obtener_dias_acumulados_funcionario(funcionario: Funcionario):
    """
    Obtiene los días acumulados (pendientes) de un funcionario.
    Función auxiliar reutilizable para cualquier funcionario.
    
    Returns:
        Dict con información de días acumulados
    """
    if not funcionario:
        return {
            'dias_disponibles': 0,
            'dias_habiles_pendientes': 0,
            'dias_calendario_pendientes': 0,
            'tipo_calculo': 'No definido',
        }
    
    tipo_calculo = obtener_tipo_calculo_dias(funcionario)
    dias_habiles_pendientes = 0
    dias_calendario_pendientes = 0
    
    periodos = PeriodoVacacional.objects.filter(funcionario=funcionario)
    
    solicitudes_aprobadas = SolicitudVacaciones.objects.filter(
        funcionario=funcionario,
        estado_solicitud__in=['aprobado', 'autorizada']
    ).select_related('periodo_vacacional', 'funcionario', 'funcionario__estamento')
    
    solicitudes_por_periodo = {}

    for solicitud in solicitudes_aprobadas:
        periodo_id = solicitud.periodo_vacacional_id
        if periodo_id not in solicitudes_por_periodo:
            solicitudes_por_periodo[periodo_id] = []
        solicitudes_por_periodo[periodo_id].append(solicitud)
    
    for periodo in periodos:
        dias_habiles_disfrutados = 0
        dias_calendario_disfrutados = 0
        
        solicitudes_periodo = solicitudes_por_periodo.get(periodo.pk, [])
        for solicitud in solicitudes_periodo:
            habiles, calendario = _calcular_dias_habiles_calendario_solicitud(solicitud)
            dias_habiles_disfrutados += habiles
            dias_calendario_disfrutados += calendario
        
        habiles_totales, calendario_totales = _obtener_tipo_dias_periodo(periodo)
        dias_habiles_pendientes_periodo = max(0, habiles_totales - dias_habiles_disfrutados)
        
        if habiles_totales > 0 and calendario_totales > 0:
            if dias_habiles_pendientes_periodo > 0:
                dias_calendario_pendientes_periodo = calendario_totales
            else:
                dias_calendario_pendientes_periodo = max(0, calendario_totales - dias_calendario_disfrutados)
        else:
            dias_calendario_pendientes_periodo = max(0, calendario_totales - dias_calendario_disfrutados)
        
        dias_habiles_pendientes += dias_habiles_pendientes_periodo
        dias_calendario_pendientes += dias_calendario_pendientes_periodo
    
    dias_pendientes_totales = dias_habiles_pendientes + dias_calendario_pendientes
    
    return {
        'dias_disponibles': dias_pendientes_totales,
        'dias_habiles_pendientes': dias_habiles_pendientes,
        'dias_calendario_pendientes': dias_calendario_pendientes,
        'tipo_calculo': tipo_calculo,
    }

def obtener_datos_dashboard_funcionario(user):
    """
    Obtiene los datos del dashboard para un funcionario regular.
    """
    try:
        funcionario = user.funcionario
    except (AttributeError, Funcionario.DoesNotExist):
        return None
    
    tipo_calculo = obtener_tipo_calculo_dias(funcionario)
    dias_habiles_pendientes = 0
    dias_calendario_pendientes = 0
    
    periodos = PeriodoVacacional.objects.filter(funcionario=funcionario)
    
    solicitudes_aprobadas = SolicitudVacaciones.objects.filter(
        funcionario=funcionario,
        estado_solicitud__in=['aprobado', 'autorizada']
    ).select_related('periodo_vacacional', 'funcionario', 'funcionario__estamento')
    
    solicitudes_por_periodo = {}

    for solicitud in solicitudes_aprobadas:
        periodo_id = solicitud.periodo_vacacional_id
        if periodo_id not in solicitudes_por_periodo:
            solicitudes_por_periodo[periodo_id] = []
        solicitudes_por_periodo[periodo_id].append(solicitud)
    
    for periodo in periodos:
        dias_habiles_disfrutados = 0
        dias_calendario_disfrutados = 0
        
        solicitudes_periodo = solicitudes_por_periodo.get(periodo.pk, [])
        for solicitud in solicitudes_periodo:
            habiles, calendario = _calcular_dias_habiles_calendario_solicitud(solicitud)
            dias_habiles_disfrutados += habiles
            dias_calendario_disfrutados += calendario
        
        habiles_totales, calendario_totales = _obtener_tipo_dias_periodo(periodo)
        dias_habiles_pendientes_periodo = max(0, habiles_totales - dias_habiles_disfrutados)

        if habiles_totales > 0 and calendario_totales > 0:
            if dias_habiles_pendientes_periodo > 0:
                dias_calendario_pendientes_periodo = calendario_totales
            else:
                dias_calendario_pendientes_periodo = max(0, calendario_totales - dias_calendario_disfrutados)
        else:
            dias_calendario_pendientes_periodo = max(0, calendario_totales - dias_calendario_disfrutados)
        
        dias_habiles_pendientes += dias_habiles_pendientes_periodo
        dias_calendario_pendientes += dias_calendario_pendientes_periodo
    
    dias_pendientes_totales = dias_habiles_pendientes + dias_calendario_pendientes
    ultimo_periodo_disfrutado_info = obtener_ultimo_periodo_disfrutado(funcionario)
    ultimo_periodo_disfrutado = None

    if ultimo_periodo_disfrutado_info:
        fecha_inicio = ultimo_periodo_disfrutado_info['fecha_inicio']
        fecha_fin = ultimo_periodo_disfrutado_info['fecha_fin']
        año_inicio = fecha_inicio.year
        año_fin = fecha_fin.year
        
        if año_inicio == año_fin:
            ultimo_periodo_disfrutado = str(año_inicio)
        else:
            ultimo_periodo_disfrutado = f"{año_inicio} - {año_fin}"
    
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
        'dias_disponibles': dias_pendientes_totales,
        'dias_habiles_pendientes': dias_habiles_pendientes,
        'dias_calendario_pendientes': dias_calendario_pendientes,
        'tipo_calculo': tipo_calculo,
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
    except (AttributeError, Funcionario.DoesNotExist):
        return None
    
    solicitudes_subordinados = SolicitudVacaciones.objects.filter(
        funcionario__jefe_inmediato=jefe_func,
        aprobaciones__etapa='JEFE',
        aprobaciones__estado='pendiente'
    ).distinct()
    
    solicitudes_creadas_por_jefe = SolicitudVacaciones.objects.filter(
        creada_por=user,
        aprobaciones__etapa='JEFE',
        aprobaciones__estado='pendiente'
    ).exclude(
        funcionario=jefe_func
    ).distinct()
    
    ids_solicitudes_pendientes = set(solicitudes_subordinados.values_list('id', flat=True))
    ids_solicitudes_pendientes.update(solicitudes_creadas_por_jefe.values_list('id', flat=True))
    total_solicitudes_pendientes = len(ids_solicitudes_pendientes)
    
    reintegros_subordinados = ReintegroVacaciones.objects.filter(
        funcionario__jefe_inmediato=jefe_func,
        aprobaciones__etapa='JEFE',
        aprobaciones__estado='pendiente'
    ).distinct()
    
    reintegros_creados_por_jefe = ReintegroVacaciones.objects.filter(
        creada_por=user,
        aprobaciones__etapa='JEFE',
        aprobaciones__estado='pendiente'
    ).exclude(
        funcionario=jefe_func
    ).distinct()
    
    ids_reintegros_pendientes = set(reintegros_subordinados.values_list('id', flat=True))
    ids_reintegros_pendientes.update(reintegros_creados_por_jefe.values_list('id', flat=True))
    total_reintegros_pendientes = len(ids_reintegros_pendientes)
    solicitudes_pendientes_gestion = total_solicitudes_pendientes + total_reintegros_pendientes
    
    solicitudes_propias_en_curso = SolicitudVacaciones.objects.filter(
        funcionario=jefe_func,
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    solicitudes_totales = SolicitudVacaciones.objects.filter(
        funcionario__jefe_inmediato=jefe_func
    ).distinct().count()
    
    dias_acumulados = obtener_dias_acumulados_funcionario(jefe_func)
    ultimo_periodo_disfrutado = obtener_ultimo_periodo_disfrutado_formateado(jefe_func)
    
    notificaciones_qs = Notificacion.objects.filter(
        funcionario=jefe_func
    ).order_by('-fecha_hora_envio')[:5]

    historiales = HistoricoAcciones.objects.filter(
        tipo_accion='solicitud',
        solicitud_vacaciones__funcionario__jefe_inmediato=jefe_func,
        nuevo_estado__in=ESTADOS_NOVEDADES_INTERES,
    ).exclude(
        usuario=user
    ).select_related(
        'solicitud_vacaciones__funcionario',
        'usuario__funcionario',
    ).order_by('-fecha_hora_accion')[:5]

    novedades = [_formatear_novedad_historial(hist) for hist in historiales]
    notificaciones = _combinar_notificaciones(notificaciones_qs, novedades)
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes_gestion,
        'solicitudes_propias_en_curso': solicitudes_propias_en_curso,
        'solicitudes_totales': solicitudes_totales,
        'dias_disponibles': dias_acumulados['dias_disponibles'],
        'dias_habiles_pendientes': dias_acumulados['dias_habiles_pendientes'],
        'dias_calendario_pendientes': dias_acumulados['dias_calendario_pendientes'],
        'tipo_calculo': dias_acumulados['tipo_calculo'],
        'ultimo_periodo_disfrutado': ultimo_periodo_disfrutado,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_coordinador(user):
    """
    Obtiene los datos del dashboard para un Coordinador Administrativo.
    """
    try:
        coord_func = user.funcionario
    except (AttributeError, Funcionario.DoesNotExist):
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
    
    notificaciones_qs = Notificacion.objects.filter(
        funcionario=coord_func
    ).order_by('-fecha_hora_envio')[:5]

    historiales = HistoricoAcciones.objects.filter(
        tipo_accion='solicitud',
        solicitud_vacaciones__funcionario__facultad_dependencia=coord_func.facultad_dependencia,
        nuevo_estado__in=ESTADOS_NOVEDADES_INTERES,
    ).exclude(
        usuario=user
    ).select_related(
        'solicitud_vacaciones__funcionario',
        'usuario__funcionario',
    ).order_by('-fecha_hora_accion')[:5]

    novedades = [_formatear_novedad_historial(hist) for hist in historiales]
    notificaciones = _combinar_notificaciones(notificaciones_qs, novedades)
    dias_acumulados = obtener_dias_acumulados_funcionario(coord_func)
    ultimo_periodo_disfrutado = obtener_ultimo_periodo_disfrutado_formateado(coord_func)
    
    solicitudes_propias_en_curso = SolicitudVacaciones.objects.filter(
        funcionario=coord_func,
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'solicitudes_propias_en_curso': solicitudes_propias_en_curso,
        'dias_disponibles': dias_acumulados['dias_disponibles'],
        'dias_habiles_pendientes': dias_acumulados['dias_habiles_pendientes'],
        'dias_calendario_pendientes': dias_acumulados['dias_calendario_pendientes'],
        'tipo_calculo': dias_acumulados['tipo_calculo'],
        'ultimo_periodo_disfrutado': ultimo_periodo_disfrutado,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_secretaria(user):
    """
    Obtiene los datos del dashboard para una Secretaria.
    """
    try:
        secretaria_func = user.funcionario
    except (AttributeError, Funcionario.DoesNotExist):
        return None
    
    solicitudes_pendientes = SolicitudVacaciones.objects.filter(
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    solicitudes_totales = SolicitudVacaciones.objects.count()
    
    notificaciones = Notificacion.objects.filter(
        funcionario=secretaria_func
    ).order_by('-fecha_hora_envio')[:5]
    
    dias_acumulados = obtener_dias_acumulados_funcionario(secretaria_func)
    ultimo_periodo_disfrutado = obtener_ultimo_periodo_disfrutado_formateado(secretaria_func)
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_totales': solicitudes_totales,
        'dias_disponibles': dias_acumulados['dias_disponibles'],
        'dias_habiles_pendientes': dias_acumulados['dias_habiles_pendientes'],
        'dias_calendario_pendientes': dias_acumulados['dias_calendario_pendientes'],
        'tipo_calculo': dias_acumulados['tipo_calculo'],
        'ultimo_periodo_disfrutado': ultimo_periodo_disfrutado,
        'notificaciones': notificaciones,
    }

def obtener_datos_dashboard_rrhh(user):
    """
    Obtiene los datos del dashboard para Recursos Humanos.
    """
    try:
        rrhh_func = user.funcionario
    except (AttributeError, Funcionario.DoesNotExist):
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
    
    solicitudes_pendientes_rrhh = SolicitudVacaciones.objects.filter(
        id__in=ids_jefe_y_coord
    ).exclude(
        aprobaciones__etapa='RRHH',
        aprobaciones__estado__in=['autorizada', 'rechazada']
    ).distinct().count()
    
    ids_reintegro_jefe_aprobada = set(
        ReintegroVacaciones.objects.filter(
            aprobaciones__etapa='JEFE',
            aprobaciones__estado='aprobada'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_reintegro_coord_aprobada = set(
        ReintegroVacaciones.objects.filter(
            aprobaciones__etapa='COORD',
            aprobaciones__estado='aprobada'
        ).values_list('id', flat=True).distinct()
    )
    
    ids_reintegro_jefe_y_coord = ids_reintegro_jefe_aprobada & ids_reintegro_coord_aprobada
    
    reintegros_pendientes_rrhh = ReintegroVacaciones.objects.filter(
        id__in=ids_reintegro_jefe_y_coord
    ).exclude(
        aprobaciones__etapa='RRHH',
        aprobaciones__estado__in=['autorizada', 'rechazada']
    ).distinct().count()
    
    solicitudes_pendientes_gestion = solicitudes_pendientes_rrhh + reintegros_pendientes_rrhh
    
    notificaciones = Notificacion.objects.filter(
        funcionario=rrhh_func
    ).order_by('-fecha_hora_envio')[:5]
    
    dias_acumulados = obtener_dias_acumulados_funcionario(rrhh_func)
    ultimo_periodo_disfrutado = obtener_ultimo_periodo_disfrutado_formateado(rrhh_func)
    
    solicitudes_propias_en_curso = SolicitudVacaciones.objects.filter(
        funcionario=rrhh_func,
        estado_solicitud__in=['pendiente', 'en_revision']
    ).count()
    
    return {
        'solicitudes_pendientes': solicitudes_pendientes_gestion,
        'solicitudes_propias_en_curso': solicitudes_propias_en_curso,
        'dias_disponibles': dias_acumulados['dias_disponibles'],
        'dias_habiles_pendientes': dias_acumulados['dias_habiles_pendientes'],
        'dias_calendario_pendientes': dias_acumulados['dias_calendario_pendientes'],
        'tipo_calculo': dias_acumulados['tipo_calculo'],
        'ultimo_periodo_disfrutado': ultimo_periodo_disfrutado,
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
