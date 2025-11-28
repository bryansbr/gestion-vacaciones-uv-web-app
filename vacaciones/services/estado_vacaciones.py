"""
Servicio para calcular y obtener el estado de vacaciones de un funcionario.
Proporciona información consolidada sobre días asignados, disfrutados y pendientes.
"""
from typing import Dict, List, Optional, Tuple
from datetime import timedelta
from django.db.models import Sum, Q
from django.utils import timezone
import holidays

from vacaciones.models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones
from usuarios.models import Funcionario

def obtener_tipo_calculo_dias(funcionario: Funcionario) -> str:
    """
    Determina el tipo de cálculo de días según el estamento y decreto del funcionario.
    
    Returns:
        str: 'Hábiles', 'Calendario', o 'Hábiles y Calendario'
    """
    estamento = funcionario.estamento.nombre.lower() if funcionario.estamento else ''
    decreto = (funcionario.decreto_resolucion or '').strip()
    
    if estamento == 'docente':
        if decreto == '1279':
            return 'Hábiles y Calendario'
        elif decreto == '115':
            return 'Calendario'
    elif estamento == 'administrativo':
        return 'Hábiles'
    elif estamento == 'trabajador oficial':
        return 'Calendario'
    
    return 'No definido'

def obtener_dias_normativos(funcionario: Funcionario) -> int:
    """
    Obtiene los días normativos asignados según el estamento del funcionario.
    
    Returns:
        int: Días normativos anuales
    """
    estamento = funcionario.estamento.nombre.lower() if funcionario.estamento else ''
    decreto = (funcionario.decreto_resolucion or '').strip()
    
    if estamento == 'docente':
        if decreto == '1279':
            return 30 
        elif decreto == '115':
            return 30
    elif estamento == 'administrativo':
        return 15
    elif estamento == 'trabajador oficial':
        return 30
    
    return 0

def _calcular_dias_habiles_calendario_solicitud(solicitud: SolicitudVacaciones) -> Tuple[int, int]:
    """
    Calcula los días hábiles y calendario de una solicitud según el estamento.
    """
    if not (solicitud.fecha_inicio_vacaciones and solicitud.fecha_fin_vacaciones):
        return 0, 0
    
    estamento = solicitud.funcionario.estamento.nombre.lower() if solicitud.funcionario.estamento else ''
    decreto = (solicitud.funcionario.decreto_resolucion or '').strip()
    
    festivos = holidays.Colombia(years=range(
        solicitud.fecha_inicio_vacaciones.year, 
        solicitud.fecha_fin_vacaciones.year + 1
    ))
    
    if estamento == 'docente' and decreto == '1279':
        actual = solicitud.fecha_inicio_vacaciones
        habiles_marcados = 0
        
        while actual <= solicitud.fecha_fin_vacaciones and habiles_marcados < 15:
            if actual.weekday() < 5 and actual not in festivos:
                habiles_marcados += 1
            actual += timedelta(days=1)
        
        dias_calendario = 0
        while actual <= solicitud.fecha_fin_vacaciones and dias_calendario < 15:
            dias_calendario += 1
            actual += timedelta(days=1)
        
        return habiles_marcados, dias_calendario
        
    elif estamento == 'administrativo':
        actual = solicitud.fecha_inicio_vacaciones
        dias_habiles = 0
        while actual <= solicitud.fecha_fin_vacaciones:
            if actual.weekday() < 5 and actual not in festivos:
                dias_habiles += 1
            actual += timedelta(days=1)
        return dias_habiles, 0
        
    elif estamento == 'docente' and decreto == '115':
        dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
        return 0, dias_calendario
        
    elif estamento == 'trabajador oficial':
        dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
        return 0, dias_calendario
    
    else:
        dias_calendario = (solicitud.fecha_fin_vacaciones - solicitud.fecha_inicio_vacaciones).days + 1
        return 0, dias_calendario


def _obtener_tipo_dias_periodo(periodo: PeriodoVacacional) -> Tuple[int, int]:
    """
    Obtiene los días hábiles y calendario totales de un periodo según el estamento.
    """
    estamento = periodo.funcionario.estamento.nombre.lower() if periodo.funcionario.estamento else ''
    decreto = (periodo.funcionario.decreto_resolucion or '').strip()
    
    if estamento == 'docente' and decreto == '1279':
        return 15, 15
    elif estamento == 'administrativo':
        return 15, 0
    elif estamento == 'docente' and decreto == '115':
        return 0, 30
    elif estamento == 'trabajador oficial':
        return 0, 30
    else:
        return 0, 0


def calcular_resumen_vacacional(funcionario: Funcionario) -> Dict:
    """
    Calcula el resumen vacacional del funcionario basándose en las solicitudes
    aprobadas/autorizadas y reintegros, no en los campos del modelo que pueden
    estar desactualizados.
    
    Returns:
        Dict con:
        - dias_totales_asignados: Suma de días totales de todos los periodos
        - dias_disfrutados: Suma de días disfrutados calculados desde solicitudes aprobadas/autorizadas
        - dias_pendientes: Suma de días pendientes calculados desde solicitudes aprobadas/autorizadas
        - numero_periodos: Número total de periodos vacacionales
        - numero_periodos_activos: Periodos con días pendientes > 0
    """
    periodos = PeriodoVacacional.objects.filter(funcionario=funcionario)
    
    dias_totales_asignados = periodos.aggregate(
        total=Sum('dias_totales_periodo')
    )['total'] or 0
    
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
    
    dias_disfrutados_totales = 0
    dias_pendientes_totales = 0
    periodos_activos = 0
    
    for periodo in periodos:
        dias_habiles_disfrutados = 0
        dias_calendario_disfrutados = 0
        
        solicitudes_periodo = solicitudes_por_periodo.get(periodo.pk, [])
        for solicitud in solicitudes_periodo:
            habiles, calendario = _calcular_dias_habiles_calendario_solicitud(solicitud)
            dias_habiles_disfrutados += habiles
            dias_calendario_disfrutados += calendario
        
        habiles_totales, calendario_totales = _obtener_tipo_dias_periodo(periodo)
        dias_habiles_pendientes = max(0, habiles_totales - dias_habiles_disfrutados)
        dias_calendario_pendientes = max(0, calendario_totales - dias_calendario_disfrutados)
        
        dias_disfrutados_periodo = dias_habiles_disfrutados + dias_calendario_disfrutados
        dias_pendientes_periodo = dias_habiles_pendientes + dias_calendario_pendientes
        
        dias_disfrutados_totales += dias_disfrutados_periodo
        dias_pendientes_totales += dias_pendientes_periodo
        
        if dias_pendientes_periodo > 0:
            periodos_activos += 1
    
    numero_periodos = periodos.count()
    
    return {
        'dias_totales_asignados': dias_totales_asignados,
        'dias_disfrutados': dias_disfrutados_totales,
        'dias_pendientes': dias_pendientes_totales,
        'numero_periodos': numero_periodos,
        'numero_periodos_activos': periodos_activos,
    }

def obtener_listado_periodos(funcionario: Funcionario) -> List[Dict]:
    """
    Obtiene el listado de periodos vacacionales con sus detalles calculados
    desde las solicitudes aprobadas/autorizadas.
    
    Returns:
        Lista de dicts con información de cada periodo
    """
    periodos = PeriodoVacacional.objects.filter(
        funcionario=funcionario
    ).order_by('-fecha_inicio_periodo')

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
    
    listado = []
    for periodo in periodos:
        dias_habiles_disfrutados = 0
        dias_calendario_disfrutados = 0
        
        solicitudes_periodo = solicitudes_por_periodo.get(periodo.pk, [])
        for solicitud in solicitudes_periodo:
            habiles, calendario = _calcular_dias_habiles_calendario_solicitud(solicitud)
            dias_habiles_disfrutados += habiles
            dias_calendario_disfrutados += calendario
        
        habiles_totales, calendario_totales = _obtener_tipo_dias_periodo(periodo)
        dias_habiles_pendientes = max(0, habiles_totales - dias_habiles_disfrutados)
        dias_calendario_pendientes = max(0, calendario_totales - dias_calendario_disfrutados)
        
        dias_disfrutados_reales = dias_habiles_disfrutados + dias_calendario_disfrutados
        dias_pendientes_reales = dias_habiles_pendientes + dias_calendario_pendientes
        
        listado.append({
            'id': periodo.id,
            'fecha_inicio': periodo.fecha_inicio_periodo,
            'fecha_fin': periodo.fecha_fin_periodo,
            'dias_totales': periodo.dias_totales_periodo,
            'dias_disfrutados': dias_disfrutados_reales,
            'dias_pendientes': dias_pendientes_reales,
        })
    
    return listado

def obtener_historial_solicitudes(funcionario: Funcionario) -> List[Dict]:
    """
    Obtiene el historial de solicitudes de vacaciones del funcionario.
    
    Returns:
        Lista de dicts con información de cada solicitud
    """
    from django.contrib.contenttypes.models import ContentType
    
    solicitudes = SolicitudVacaciones.objects.filter(
        funcionario=funcionario
    ).select_related(
        'periodo_vacacional'
    ).prefetch_related(
        'aprobaciones'
    ).order_by('-fecha_solicitud')
    
    ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
    
    historial = []
    for solicitud in solicitudes:
        motivo_rechazo = None
        
        if solicitud.estado_solicitud == 'rechazado':
            aprobacion_rechazo = solicitud.aprobaciones.filter(
                content_type=ct_solicitud,
                object_id=solicitud.pk,
                etapa='RRHH',
                estado='rechazada'
            ).first()
            
            if aprobacion_rechazo and aprobacion_rechazo.observacion:
                motivo_rechazo = aprobacion_rechazo.observacion.strip()
        
        historial.append({
            'id': solicitud.id,
            'codigo_sabs': solicitud.codigo_sabs,
            'fecha_solicitud': solicitud.fecha_solicitud,
            'fecha_inicio_vacaciones': solicitud.fecha_inicio_vacaciones,
            'fecha_fin_vacaciones': solicitud.fecha_fin_vacaciones,
            'total_dias_solicitados': solicitud.total_dias_solicitados,
            'estado_solicitud': solicitud.estado_solicitud,
            'estado_display': dict(solicitud.ESTADOS).get(solicitud.estado_solicitud, solicitud.estado_solicitud),
            'periodo_vacacional_id': solicitud.periodo_vacacional.id if solicitud.periodo_vacacional else None,
            'periodo_vacacional_anio': solicitud.periodo_vacacional.fecha_inicio_periodo.year if solicitud.periodo_vacacional else None,
            'motivo_rechazo': motivo_rechazo,
        })
    
    return historial

def obtener_historial_reintegros(funcionario: Funcionario) -> List[Dict]:
    """
    Obtiene el historial de reintegros de vacaciones del funcionario.
    
    Returns:
        Lista de dicts con información de cada reintegro
    """
    reintegros = ReintegroVacaciones.objects.filter(
        funcionario=funcionario
    ).select_related(
        'periodo_vacacional',
        'solicitud_vacaciones'
    ).order_by('-fecha_solicitud')
    
    historial = []
    for reintegro in reintegros:
        historial.append({
            'id': reintegro.id,
            'codigo_sabs': reintegro.codigo_sabs,
            'fecha_solicitud': reintegro.fecha_solicitud,
            'fecha_reintegro': reintegro.fecha_reintegro,
            'fecha_disfrute_desde': reintegro.fecha_disfrute_desde,
            'fecha_disfrute_hasta': reintegro.fecha_disfrute_hasta,
            'dias_disfrutados': reintegro.dias_disfrutados,
            'dias_pendientes': reintegro.dias_pendientes,
            'motivo_reintegro': reintegro.motivo_reintegro,
            'motivo_display': dict(reintegro.MOTIVOS_REINTEGRO).get(reintegro.motivo_reintegro, reintegro.motivo_reintegro),
            'estado_solicitud': reintegro.estado_solicitud,
            'estado_display': dict(reintegro.ESTADOS).get(reintegro.estado_solicitud, reintegro.estado_solicitud),
            'es_reintegro_anticipado': reintegro.es_reintegro_anticipado,
            'periodo_vacacional_id': reintegro.periodo_vacacional.id if reintegro.periodo_vacacional else None,
            'solicitud_vacaciones_codigo': reintegro.solicitud_vacaciones.codigo_sabs if reintegro.solicitud_vacaciones else None,
        })
    
    return historial

def obtener_estado_completo_vacaciones(funcionario: Funcionario) -> Dict:
    """
    Obtiene el estado completo de vacaciones del funcionario.
    Consolida toda la información necesaria para el módulo de estado.
    
    Returns:
        Dict con toda la información del estado de vacaciones
    """
    if not funcionario:
        return {}
    
    resumen = calcular_resumen_vacacional(funcionario)
    listado_periodos = obtener_listado_periodos(funcionario)
    historial_solicitudes = obtener_historial_solicitudes(funcionario)
    historial_reintegros = obtener_historial_reintegros(funcionario)
    
    datos_regimen = {
        'estamento': funcionario.estamento.nombre if funcionario.estamento else 'No definido',
        'tipo_calculo': obtener_tipo_calculo_dias(funcionario),
        'dias_normativos': obtener_dias_normativos(funcionario),
        'decreto_resolucion': funcionario.decreto_resolucion or 'N/A',
    }
    
    return {
        'funcionario': {
            'id': funcionario.id,
            'nombre_completo': f"{funcionario.nombre} {funcionario.apellido}",
            'numero_identificacion': funcionario.numero_identificacion,
            'facultad_dependencia': funcionario.facultad_dependencia.nombre if funcionario.facultad_dependencia else 'No asignada',
        },
        'resumen_vacacional': resumen,
        'listado_periodos': listado_periodos,
        'historial_solicitudes': historial_solicitudes,
        'historial_reintegros': historial_reintegros,
        'datos_regimen': datos_regimen,
    }
