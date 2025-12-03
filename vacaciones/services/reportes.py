"""
Servicio de reportes para el módulo de vacaciones.
Proporciona funciones para calcular estadísticas y métricas de solicitudes y reintegros.
"""
from core.permissions import (
    es_jefe_inmediato,
    es_secretaria,
    es_coordinador_administrativo,
    es_rrhh
)
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.utils import timezone
from vacaciones.models import SolicitudVacaciones, ReintegroVacaciones

def _filtrar_por_rol(queryset_solicitudes, queryset_reintegros, user):
    """
    Filtra los querysets según el rol del usuario.
    
    Restricciones:
    - Jefe Inmediato: solo funcionarios a su cargo (subordinados)
    - Secretaria: solo funcionarios bajo su jefe inmediato
    - Coordinación Administrativa: solo su Facultad/Dependencia
    - RRHH: todos los funcionarios
    """
    
    if es_rrhh(user):
        return queryset_solicitudes, queryset_reintegros
    
    user_func = getattr(user, 'funcionario', None)
    if not user_func:
        return queryset_solicitudes.none(), queryset_reintegros.none()
    
    elif es_coordinador_administrativo(user):
        qs_sol = queryset_solicitudes.filter(
            funcionario__facultad_dependencia=user_func.facultad_dependencia
        )
        qs_rein = queryset_reintegros.filter(
            funcionario__facultad_dependencia=user_func.facultad_dependencia
        )
        return qs_sol, qs_rein
    
    elif es_jefe_inmediato(user):
        qs_sol = queryset_solicitudes.filter(
            funcionario__jefe_inmediato=user_func
        )
        qs_rein = queryset_reintegros.filter(
            funcionario__jefe_inmediato=user_func
        )
        return qs_sol, qs_rein
    
    elif es_secretaria(user):
        if user_func.jefe_inmediato:
            qs_sol = queryset_solicitudes.filter(
                funcionario__jefe_inmediato=user_func.jefe_inmediato
            )
            qs_rein = queryset_reintegros.filter(
                funcionario__jefe_inmediato=user_func.jefe_inmediato
            )
            return qs_sol, qs_rein
        else:
            return queryset_solicitudes.none(), queryset_reintegros.none()
    
    else:
        qs_sol = queryset_solicitudes.filter(funcionario=user_func)
        qs_rein = queryset_reintegros.filter(funcionario=user_func)
        return qs_sol, qs_rein

def obtener_estadisticas_solicitudes(user, fecha_inicio=None, fecha_fin=None, facultad_id=None):
    """
    Calcula estadísticas generales de solicitudes según el rol del usuario.
    
    Args:
        user: Usuario autenticado
        fecha_inicio: Fecha de inicio para filtrar (opcional)
        fecha_fin: Fecha de fin para filtrar (opcional)
        facultad_id: ID de facultad para filtrar (opcional, solo para RRHH)
    
    Returns:
        Dict con estadísticas de solicitudes
    """
    queryset = SolicitudVacaciones.objects.select_related(
        'funcionario', 'funcionario__facultad_dependencia'
    )
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    if facultad_id:
        queryset = queryset.filter(funcionario__facultad_dependencia_id=facultad_id)
    
    queryset, _ = _filtrar_por_rol(queryset, ReintegroVacaciones.objects.none(), user)
    
    return {
        'solicitudes_aprobadas': queryset.filter(estado_solicitud='aprobado').count(),
        'solicitudes_devueltas': queryset.filter(estado_solicitud='devuelta').count(),
        'solicitudes_autorizadas': queryset.filter(estado_solicitud='autorizada').count(),
        'solicitudes_rechazadas': queryset.filter(estado_solicitud='rechazado').count(),
        'solicitudes_pendientes': queryset.filter(
            estado_solicitud__in=['pendiente', 'en_revision']
        ).count(),
        'solicitudes_totales': queryset.count(),
    }

def obtener_solicitudes_por_facultad(user, fecha_inicio=None, fecha_fin=None):
    """
    Agrupa solicitudes por facultad/dependencia según el rol del usuario.
    
    Returns:
        Lista de dicts con {'facultad': str, 'total': int, 'por_estado': dict}
    """
    queryset = SolicitudVacaciones.objects.select_related(
        'funcionario__facultad_dependencia'
    )
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    queryset, _ = _filtrar_por_rol(queryset, ReintegroVacaciones.objects.none(), user)
    
    resultados_agrupados = queryset.values(
        'funcionario__facultad_dependencia__nombre'
    ).annotate(
        total=Count('id'),
        aprobadas=Count('id', filter=Q(estado_solicitud='aprobado')),
        devueltas=Count('id', filter=Q(estado_solicitud='devuelta')),
        autorizadas=Count('id', filter=Q(estado_solicitud='autorizada')),
        rechazadas=Count('id', filter=Q(estado_solicitud='rechazado')),
        pendientes=Count('id', filter=Q(estado_solicitud__in=['pendiente', 'en_revision'])),
    ).order_by('funcionario__facultad_dependencia__nombre')
    
    resultados = []
    for item in resultados_agrupados:
        resultados.append({
            'facultad': item['funcionario__facultad_dependencia__nombre'] or 'Sin asignar',
            'total': item['total'],
            'por_estado': {
                'aprobado': item['aprobadas'],
                'devuelta': item['devueltas'],
                'autorizada': item['autorizadas'],
                'rechazado': item['rechazadas'],
                'pendiente': item['pendientes'],
            }
        })
    
    return resultados

def obtener_solicitudes_por_anio(user, anio=None, fecha_inicio=None, fecha_fin=None):
    """
    Agrupa solicitudes por año según el rol del usuario.
    
    Args:
        user: Usuario autenticado
        anio: Año específico para filtrar (opcional)
        fecha_inicio: Fecha de inicio para filtrar (opcional)
        fecha_fin: Fecha de fin para filtrar (opcional)
    
    Returns:
        Lista de dicts con {'anio': int, 'total': int, 'por_estado': dict}
    """
    queryset = SolicitudVacaciones.objects.all()
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    if anio:
        queryset = queryset.filter(fecha_solicitud__year=anio)
    
    queryset, _ = _filtrar_por_rol(queryset, ReintegroVacaciones.objects.none(), user)

    resultados = queryset.annotate(
        anio=ExtractYear('fecha_solicitud')
    ).values('anio', 'estado_solicitud').annotate(
        total=Count('id')
    ).order_by('anio')
    
    por_anio = {}
    for item in resultados:
        anio_val = item['anio']
        if anio_val is None:
            continue
        if anio_val not in por_anio:
            por_anio[anio_val] = {
                'anio': anio_val,
                'total': 0,
                'por_estado': {}
            }
        por_anio[anio_val]['total'] += item['total']
        por_anio[anio_val]['por_estado'][item['estado_solicitud']] = item['total']
    
    return list(por_anio.values())

def obtener_funcionarios_en_vacaciones(user, fecha_consulta=None):
    """
    Obtiene funcionarios que están actualmente en vacaciones según el rol del usuario.
    
    Returns:
        Lista de dicts con información de funcionarios en vacaciones
    """
    if not fecha_consulta:
        fecha_consulta = timezone.now().date()
    
    queryset = SolicitudVacaciones.objects.filter(
        estado_solicitud='autorizada',
        fecha_inicio_vacaciones__lte=fecha_consulta,
        fecha_fin_vacaciones__gte=fecha_consulta
    ).select_related(
        'funcionario',
        'funcionario__facultad_dependencia'
    )
    
    queryset, _ = _filtrar_por_rol(queryset, ReintegroVacaciones.objects.none(), user)
    
    funcionarios = []
    for solicitud in queryset:
        funcionarios.append({
            'funcionario': solicitud.funcionario,
            'solicitud': solicitud,
            'codigo_sabs': solicitud.codigo_sabs,
            'fecha_inicio': solicitud.fecha_inicio_vacaciones,
            'fecha_fin': solicitud.fecha_fin_vacaciones,
            'dias_solicitados': solicitud.total_dias_solicitados,
            'facultad': solicitud.funcionario.facultad_dependencia.nombre if solicitud.funcionario.facultad_dependencia else 'Sin asignar',
            'nombre_completo': f"{solicitud.funcionario.nombre} {solicitud.funcionario.apellido}",
        })
    
    return funcionarios

def obtener_estadisticas_reintegros(user, fecha_inicio=None, fecha_fin=None, facultad_id=None):
    """
    Calcula estadísticas generales de reintegros según el rol del usuario.
    
    Args:
        user: Usuario autenticado
        fecha_inicio: Fecha de inicio para filtrar (opcional)
        fecha_fin: Fecha de fin para filtrar (opcional)
        facultad_id: ID de facultad para filtrar (opcional, solo para RRHH)
    
    Returns:
        Dict con estadísticas de reintegros
    """
    queryset = ReintegroVacaciones.objects.select_related(
        'funcionario', 'funcionario__facultad_dependencia'
    )
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    if facultad_id:
        queryset = queryset.filter(funcionario__facultad_dependencia_id=facultad_id)
    
    _, queryset = _filtrar_por_rol(SolicitudVacaciones.objects.none(), queryset, user)
    
    return {
        'reintegros_aprobados': queryset.filter(estado_solicitud='aprobado').count(),
        'reintegros_devueltos': queryset.filter(estado_solicitud='devuelta').count(),
        'reintegros_autorizados': queryset.filter(estado_solicitud='autorizada').count(),
        'reintegros_rechazados': queryset.filter(estado_solicitud='rechazado').count(),
        'reintegros_pendientes': queryset.filter(
            estado_solicitud__in=['pendiente', 'en_revision']
        ).count(),
        'reintegros_completados': queryset.filter(estado_solicitud='completado').count(),
        'reintegros_cancelados': queryset.filter(estado_solicitud='cancelado').count(),
        'reintegros_totales': queryset.count(),
    }

def obtener_reintegros_por_facultad(user, fecha_inicio=None, fecha_fin=None):
    """
    Agrupa reintegros por facultad/dependencia según el rol del usuario.
    
    Returns:
        Lista de dicts con {'facultad': str, 'total': int, 'por_estado': dict}
    """
    queryset = ReintegroVacaciones.objects.select_related(
        'funcionario__facultad_dependencia'
    )
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    _, queryset = _filtrar_por_rol(SolicitudVacaciones.objects.none(), queryset, user)
    
    resultados_agrupados = queryset.values(
        'funcionario__facultad_dependencia__nombre'
    ).annotate(
        total=Count('id'),
        aprobados=Count('id', filter=Q(estado_solicitud='aprobado')),
        devueltos=Count('id', filter=Q(estado_solicitud='devuelta')),
        autorizados=Count('id', filter=Q(estado_solicitud='autorizada')),
        rechazados=Count('id', filter=Q(estado_solicitud='rechazado')),
        pendientes=Count('id', filter=Q(estado_solicitud__in=['pendiente', 'en_revision'])),
        completados=Count('id', filter=Q(estado_solicitud='completado')),
        cancelados=Count('id', filter=Q(estado_solicitud='cancelado')),
    ).order_by('funcionario__facultad_dependencia__nombre')
    
    resultados = []
    for item in resultados_agrupados:
        resultados.append({
            'facultad': item['funcionario__facultad_dependencia__nombre'] or 'Sin asignar',
            'total': item['total'],
            'por_estado': {
                'aprobado': item['aprobados'],
                'devuelta': item['devueltos'],
                'autorizada': item['autorizados'],
                'rechazado': item['rechazados'],
                'pendiente': item['pendientes'],
                'completado': item['completados'],
                'cancelado': item['cancelados'],
            }
        })
    
    return resultados

def obtener_reintegros_por_anio(user, anio=None, fecha_inicio=None, fecha_fin=None):
    """
    Agrupa reintegros por año según el rol del usuario.
    
    Args:
        user: Usuario autenticado
        anio: Año específico para filtrar (opcional)
        fecha_inicio: Fecha de inicio para filtrar (opcional)
        fecha_fin: Fecha de fin para filtrar (opcional)
    
    Returns:
        Lista de dicts con {'anio': int, 'total': int, 'por_estado': dict}
    """
    queryset = ReintegroVacaciones.objects.all()
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    
    if anio:
        queryset = queryset.filter(fecha_solicitud__year=anio)
    
    _, queryset = _filtrar_por_rol(SolicitudVacaciones.objects.none(), queryset, user)

    resultados = queryset.annotate(
        anio=ExtractYear('fecha_solicitud')
    ).values('anio', 'estado_solicitud').annotate(
        total=Count('id')
    ).order_by('anio')
    
    por_anio = {}
    for item in resultados:
        anio_val = item['anio']
        if anio_val is None:
            continue
        if anio_val not in por_anio:
            por_anio[anio_val] = {
                'anio': anio_val,
                'total': 0,
                'por_estado': {}
            }
        por_anio[anio_val]['total'] += item['total']
        por_anio[anio_val]['por_estado'][item['estado_solicitud']] = item['total']
    
    return list(por_anio.values())

def obtener_reintegros_anticipados(user, fecha_inicio=None, fecha_fin=None, facultad_id=None):
    """
    Obtiene estadísticas de reintegros anticipados según el rol del usuario.
    
    Returns:
        Dict con estadísticas de reintegros anticipados
    """
    queryset = ReintegroVacaciones.objects.filter(
        es_reintegro_anticipado=True
    ).select_related(
        'funcionario',
        'funcionario__facultad_dependencia'
    )
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_solicitud__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_solicitud__lte=fecha_fin)
    if facultad_id:
        queryset = queryset.filter(funcionario__facultad_dependencia_id=facultad_id)
    
    _, queryset = _filtrar_por_rol(SolicitudVacaciones.objects.none(), queryset, user)
    por_estado = {}
    estados = ['pendiente', 'en_revision', 'devuelta', 'aprobado', 'autorizada', 'rechazado', 'cancelado', 'completado']
    for estado in estados:
        por_estado[estado] = queryset.filter(estado_solicitud=estado).count()
    
    return {
        'total_reintegros_anticipados': queryset.count(),
        'por_estado': por_estado,
        'detalle': list(queryset.values(
            'id',
            'codigo_sabs',
            'fecha_solicitud',
            'fecha_reintegro',
            'estado_solicitud',
            'funcionario__nombre',
            'funcionario__apellido',
            'funcionario__facultad_dependencia__nombre'
        )[:100])
    }

def obtener_reporte_completo(user, fecha_inicio=None, fecha_fin=None, facultad_id=None):
    """
    Genera un reporte completo con todas las métricas según el rol del usuario.
    
    Returns:
        Dict con todas las estadísticas separadas para solicitudes y reintegros
    """
    return {
        'estadisticas_solicitudes': obtener_estadisticas_solicitudes(
            user, fecha_inicio, fecha_fin, facultad_id
        ),
        'solicitudes_por_facultad': obtener_solicitudes_por_facultad(
            user, fecha_inicio, fecha_fin
        ),
        'solicitudes_por_anio': obtener_solicitudes_por_anio(user, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
        'funcionarios_en_vacaciones': obtener_funcionarios_en_vacaciones(user),
        'estadisticas_reintegros': obtener_estadisticas_reintegros(
            user, fecha_inicio, fecha_fin, facultad_id
        ),
        'reintegros_por_facultad': obtener_reintegros_por_facultad(
            user, fecha_inicio, fecha_fin
        ),
        'reintegros_por_anio': obtener_reintegros_por_anio(user, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin),
        'reintegros_anticipados': obtener_reintegros_anticipados(
            user, fecha_inicio, fecha_fin, facultad_id
        ),
    }
