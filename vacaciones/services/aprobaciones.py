import logging
from typing import Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from notificaciones.models import Notificacion
from ..models import AprobacionEtapa, CustomUser, HistoricoAcciones, SolicitudVacaciones
logger = logging.getLogger(__name__)



# -----------------------------------------------------------
# Constantes
# -----------------------------------------------------------
# Límite máximo para campos de observación
MAX_OBSERVACION_LENGTH = 2000

# Separador para observaciones de reenvío por funcionario
SEPARADOR_REENVIO_FUNCIONARIO = "\n\n--- Reenvío por funcionario ---\n"

# Margen de seguridad para truncamiento de observaciones
MARGEN_SEGURIDAD_OBSERVACION = 50

# -----------------------------------------------------------
# Utilidades
# -----------------------------------------------------------
ETAPA_HUMANA = {
    'JEFE':  'Jefe Inmediato',
    'COORD': 'Coordinación Administrativa',
    'RRHH':  'División de Recursos Humanos',
}

ESTADO_GLOBAL_MAP = {
    'autorizada': 'aprobado',
    'rechazada':  'rechazado',
    'devuelta':   'pendiente',
    'en_progreso': 'en_revision',
    'desconocido': 'en_revision',
}

def _etapa_siguiente(codigo: str) -> Optional[str]:
    orden = list(SolicitudVacaciones.ETAPAS_ORDEN)
    try:
        idx = orden.index(codigo)
    except ValueError:
        return None
    return orden[idx + 1] if idx + 1 < len(orden) else None

def _validar_propietario_o_permiso(user: CustomUser, solicitud: SolicitudVacaciones, etapa: str):
    """
    Base:
    - El funcionario dueño puede ver, pero NO transicionar.
    - JEFE ⇒ grupo 'Jefe Inmediato' o permiso 'dar_visto_bueno_solicitud'
    - COORD ⇒ grupo 'Coordinador Administrativo' o permiso 'dar_visto_bueno_solicitud'
    - RRHH  ⇒ grupo 'Recursos Humanos' o permiso 'autorizar_solicitud' / 'rechazar_solicitud' o email de RRHH
    """

    if etapa == 'JEFE' and not (user.has_perm('vacaciones.dar_visto_bueno_solicitud') or user.groups.filter(name__in=['Jefe Inmediato', 'JEFE_INMEDIATO']).exists()):
        raise PermissionDenied("No tienes permisos para aprobar/devolver como Jefe Inmediato.")
    if etapa == 'COORD' and not (user.has_perm('vacaciones.dar_visto_bueno_solicitud') or user.groups.filter(name__in=['Coordinador Administrativo', 'COORD_ADMIN']).exists()):
        raise PermissionDenied("No tienes permisos para aprobar/devolver como Coordinación Administrativa.")
    if etapa == 'RRHH':
        tiene_permiso = (
            user.has_perm('vacaciones.autorizar_solicitud') or 
            user.has_perm('vacaciones.rechazar_solicitud') or 
            user.groups.filter(name='Recursos Humanos').exists() or
            (hasattr(user, 'email') and user.email and "recursos.humanos" in user.email.lower())
        )
        if not tiene_permiso:
            raise PermissionDenied("No tienes permisos para autorizar/rechazar como RRHH.")

def _refrescar_estado_global(solicitud: SolicitudVacaciones):
    """
    Lee el estado derivado de las etapas y sincroniza el campo existente solicitud.estado_solicitud
    con la taxonomía del modelo (aprobado/en_revision/rechazado).
    """
    global_derivado = solicitud.estado_global
    solicitud.estado_solicitud = ESTADO_GLOBAL_MAP.get(global_derivado, 'en_revision')
    solicitud.save(update_fields=['estado_solicitud'])

def _registrar_historial(
    *,
    solicitud: SolicitudVacaciones,
    usuario: CustomUser,
    accion: str,
    grupo_autorizador: str,
    nuevo_estado: str,
    estado_anterior: str,
    observacion: Optional[str] = None,
):
    HistoricoAcciones.objects.create(
        accion_realizada=accion,
        tipo_accion='solicitud',
        usuario=usuario,
        solicitud_vacaciones=solicitud,
        grupo_autorizador=grupo_autorizador,
        nuevo_estado=nuevo_estado,
        estado_anterior=estado_anterior,
        observacion=observacion or '',
    )

def _get_etapa_activa_estricta(solicitud: SolicitudVacaciones) -> AprobacionEtapa:
    etapa_activa = solicitud.etapa_activa

    if not etapa_activa:
        raise ValidationError("No hay etapa activa para transicionar.")
    return etapa_activa

def _concatenar_observacion_con_limite(observacion_actual: str, nueva_observacion: str, separador: str = SEPARADOR_REENVIO_FUNCIONARIO) -> str:
    """
    Concatena una nueva observación con la observación actual, respetando el límite máximo.
    
    Args:
        observacion_actual: Observación existente
        nueva_observacion: Nueva observación a agregar
        separador: Separador entre observaciones
        
    Returns:
        Observación concatenada respetando MAX_OBSERVACION_LENGTH
    """
    observacion_actual = observacion_actual or ''
    nueva_observacion_formateada = f"{separador}{nueva_observacion.strip()}"
    observacion_completa = observacion_actual + nueva_observacion_formateada
    
    if len(observacion_completa) <= MAX_OBSERVACION_LENGTH:
        return observacion_completa
    
    espacio_disponible = MAX_OBSERVACION_LENGTH - len(nueva_observacion_formateada) - MARGEN_SEGURIDAD_OBSERVACION
    
    if espacio_disponible > 0:
        observacion_truncada = observacion_actual[-espacio_disponible:] if observacion_actual else ''
        return observacion_truncada + nueva_observacion_formateada
    else:
        return nueva_observacion_formateada

# -----------------------------------------------------------
# Transiciones (API pública servicio)
# -----------------------------------------------------------
@transaction.atomic
def aprobar_etapa(user: CustomUser, solicitud: SolicitudVacaciones, observacion: Optional[str] = None) -> AprobacionEtapa:
    """
    JEFE/COORD: pendiente → aprobada
    Solo se puede aprobar la ETAPA ACTIVA y si no hay rojos previos.
    """
    etapa = _get_etapa_activa_estricta(solicitud)
    if etapa.etapa not in ('JEFE', 'COORD'):
        raise ValidationError("La aprobación de etapa aplica únicamente para Jefe Inmediato o Coordinación.")

    _validar_propietario_o_permiso(user, solicitud, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError(f"La etapa actual ({ETAPA_HUMANA[etapa.etapa]}) no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'aprobada'
    etapa.observacion = observacion or ''
    etapa.actualizado_por = user
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    _registrar_historial(
        solicitud=solicitud,
        usuario=user,
        accion='aprobacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    _refrescar_estado_global(solicitud)

    return etapa

@transaction.atomic
def devolver_etapa(user: CustomUser, solicitud: SolicitudVacaciones, observacion: str) -> AprobacionEtapa:
    """
    JEFE/COORD: pendiente → devuelta (requiere observación)
    Cuando se devuelve, la solicitud queda en estado 'pendiente' para que el funcionario pueda corregirla.
    Al devolver, todas las etapas se reinician a 'pendiente' para que el flujo vuelva a empezar desde el inicio.
    """
    if not observacion or not observacion.strip():
        raise ValidationError("Debes proporcionar el motivo de la devolución.")

    etapa = _get_etapa_activa_estricta(solicitud)

    if etapa.etapa not in ('JEFE', 'COORD'):
        raise ValidationError("La devolución aplica únicamente para Jefe Inmediato o Coordinación.")

    _validar_propietario_o_permiso(user, solicitud, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError(f"La etapa actual ({ETAPA_HUMANA[etapa.etapa]}) no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'devuelta'
    etapa.observacion = observacion.strip()
    etapa.actualizado_por = user
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    # Cuando JEFE o COORD devuelven, todas las etapas se reinician para que el flujo empiece desde cero
    for etapa_a_reiniciar in solicitud.aprobaciones.all():
        if etapa_a_reiniciar.etapa != etapa.etapa:
            etapa_a_reiniciar.estado = 'pendiente'
            etapa_a_reiniciar.observacion = ''
            etapa_a_reiniciar.actualizado_por = None
            etapa_a_reiniciar.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    _registrar_historial(
        solicitud=solicitud,
        usuario=user,
        accion='observacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    solicitud.estado_solicitud = 'pendiente'
    solicitud.save(update_fields=['estado_solicitud'])

    return etapa

@transaction.atomic
def autorizar_rrhh(user: CustomUser, solicitud: SolicitudVacaciones, observacion: Optional[str] = None) -> AprobacionEtapa:
    """
    RRHH: pendiente → autorizada (aprobación final)
    Solo cuando JEFE y COORD estén 'aprobada'.
    """
    etapa = _get_etapa_activa_estricta(solicitud)

    if etapa.etapa != 'RRHH':
        raise ValidationError("Solo RRHH puede autorizar en la etapa RRHH.")

    _validar_propietario_o_permiso(user, solicitud, etapa.etapa)

    req = {a.etapa: a.estado for a in solicitud.aprobaciones.all()}

    if not (req.get('JEFE') == 'aprobada' and req.get('COORD') == 'aprobada'):
        raise ValidationError("No puedes autorizar: JEFE y COORD deben estar aprobadas primero.")

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa de RRHH no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'autorizada'
    etapa.observacion = observacion or ''
    etapa.actualizado_por = user
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    _registrar_historial(
        solicitud=solicitud,
        usuario=user,
        accion='aprobacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    _refrescar_estado_global(solicitud)
    return etapa

@transaction.atomic
def rechazar_rrhh(user: CustomUser, solicitud: SolicitudVacaciones, observacion: str) -> AprobacionEtapa:
    """
    RRHH: pendiente → rechazada (requiere observación).
    Deja la solicitud en estado final (no reenviable).
    Envía notificaciones al funcionario, C.A. y Jefe Inmediato.
    """
    if not observacion or not observacion.strip():
        raise ValidationError("Debes proporcionar el motivo del rechazo.")

    etapa = _get_etapa_activa_estricta(solicitud)

    if etapa.etapa != 'RRHH':
        raise ValidationError("Solo RRHH puede rechazar en la etapa RRHH.")

    _validar_propietario_o_permiso(user, solicitud, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa de RRHH no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'rechazada'
    etapa.observacion = observacion.strip()
    etapa.actualizado_por = user
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    _registrar_historial(
        solicitud=solicitud,
        usuario=user,
        accion='rechazo',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    _refrescar_estado_global(solicitud)  # → 'rechazado'

    try:
        funcionario = solicitud.funcionario
        jefe_inmediato = funcionario.jefe_inmediato
        
        aprobacion_coord = solicitud.aprobaciones.filter(etapa='COORD', estado='aprobada').first()
        coord_funcionario = None
        if aprobacion_coord and aprobacion_coord.actualizado_por:
            coord_funcionario = getattr(aprobacion_coord.actualizado_por, 'funcionario', None)
        
        mensaje = (
            f"La solicitud de vacaciones {solicitud.codigo_sabs} ha sido rechazada por Recursos Humanos.\n\n"
            f"Motivo del rechazo: {observacion.strip()}\n\n"
            f"Periodo solicitado: {solicitud.fecha_inicio_vacaciones.strftime('%d/%m/%Y')} - "
            f"{solicitud.fecha_fin_vacaciones.strftime('%d/%m/%Y')}\n"
            f"Días solicitados: {solicitud.total_dias_solicitados}"
        )
        
        Notificacion.objects.create(
            asunto=f"Solicitud de vacaciones {solicitud.codigo_sabs} rechazada",
            mensaje=mensaje,
            funcionario=funcionario,
            solicitud_vacaciones=solicitud,
            tipo_notificacion="solicitud",
        )
        
        if jefe_inmediato:
            Notificacion.objects.create(
                asunto=f"Solicitud de vacaciones {solicitud.codigo_sabs} rechazada",
                mensaje=mensaje,
                funcionario=jefe_inmediato,
                funcionario_cc=funcionario,
                solicitud_vacaciones=solicitud,
                tipo_notificacion="solicitud",
            )
        
        if coord_funcionario:
            Notificacion.objects.create(
                asunto=f"Solicitud de vacaciones {solicitud.codigo_sabs} rechazada",
                mensaje=mensaje,
                funcionario=coord_funcionario,
                funcionario_cc=funcionario,
                solicitud_vacaciones=solicitud,
                tipo_notificacion="solicitud",
            )
    except Exception as exc:
        logger.exception(
            "Error al enviar notificaciones de rechazo para la solicitud %s: %s",
            solicitud.codigo_sabs,
            exc,
        )

    return etapa

@transaction.atomic
def enviar_al_proximo_revisor(user: CustomUser, solicitud: SolicitudVacaciones, observacion: Optional[str] = None) -> AprobacionEtapa:
    """
    Envía la solicitud al próximo revisor después de que una etapa ha sido aprobada.
    Solo puede ser llamada por el usuario que aprobó la etapa anterior.
    Ejemplo: Jefe Inmediato aprueba JEFE, luego puede enviar la solicitud a COORD.
    
    Requisitos:
    - La etapa actual (JEFE o COORD) debe estar aprobada.
    - La siguiente etapa (COORD o RRHH) debe estar pendiente.
    - El usuario debe haber aprobado la etapa anterior.
    """
    mapa = {a.etapa: a for a in solicitud.aprobaciones.all()}
    
    etapa_aprobada = None
    etapa_siguiente = None
    
    if mapa.get('JEFE') and mapa['JEFE'].estado == 'aprobada' and mapa.get('COORD') and mapa['COORD'].estado == 'pendiente':
        etapa_aprobada = mapa['JEFE']
        etapa_siguiente = mapa['COORD']
    elif mapa.get('COORD') and mapa['COORD'].estado == 'aprobada' and mapa.get('RRHH') and mapa['RRHH'].estado == 'pendiente':
        etapa_aprobada = mapa['COORD']
        etapa_siguiente = mapa['RRHH']
    else:
        raise ValidationError("No se puede enviar al próximo revisor: la etapa actual debe estar aprobada y la siguiente pendiente.")
    
    if etapa_aprobada.actualizado_por_id != user.id and not user.is_superuser:
        raise PermissionDenied("Solo el usuario que aprobó la etapa anterior puede enviar la solicitud al próximo revisor.")
    
    solicitud.estado_solicitud = 'en_revision'
    solicitud.save(update_fields=['estado_solicitud'])
    
    _registrar_historial(
        solicitud=solicitud,
        usuario=user,
        accion='observacion',
        grupo_autorizador=ETAPA_HUMANA[etapa_aprobada.etapa],
        nuevo_estado='enviada',
        estado_anterior='aprobada',
        observacion=observacion or f'Enviada al {ETAPA_HUMANA[etapa_siguiente.etapa]}',
    )
    
    return etapa_siguiente

@transaction.atomic
def reenviar_funcionario(user: CustomUser, solicitud: SolicitudVacaciones, observacion: Optional[str] = None) -> Optional[AprobacionEtapa]:
    """
    Envío/Reenvío de solicitud:
    - Puede enviar: el funcionario dueño o quien creó la solicitud (Secretaria/Jefe Inmediato) O superusuario.
    - Casos:
      a) Solicitud devuelta: hay etapas devueltas, las vuelve a 'pendiente'.
      b) Solicitud nueva: no hay etapas devueltas, simplemente cambia el estado a 'en_revision'.
    - Cambia el estado de la solicitud a 'en_revision' para indicar que está en el flujo.
    - No aplica si la solicitud quedó 'rechazada' por RRHH (flujo final).
    """

    puede_reenviar = (
        solicitud.funcionario.user_id == user.id or
        (solicitud.creada_por_id and solicitud.creada_por_id == user.id) or
        user.is_superuser
    )

    if not puede_reenviar:
        raise PermissionDenied("No tiene permisos para enviar/reenviar esta solicitud.")

    if solicitud.estado_global == 'rechazada':
        raise ValidationError("No se puede reenviar una solicitud rechazada por RRHH.")

    if solicitud.estado_solicitud not in ('pendiente',) and solicitud.estado_global != 'devuelta':
        raise ValidationError("Solo se pueden enviar solicitudes en estado 'pendiente' o devueltas.")

    devueltas = solicitud.aprobaciones.filter(estado='devuelta', etapa__in=('JEFE', 'COORD'))
    
    if devueltas.exists():
        etapa = devueltas.first()
        
        # Cuando hay etapas devueltas, reiniciar todas las etapas devueltas a 'pendiente'
        etapas_devueltas_list = list(devueltas)
        for etapa_devuelta in etapas_devueltas_list:
            estado_anterior = etapa_devuelta.estado
            etapa_devuelta.estado = 'pendiente'
            
            if observacion:
                etapa_devuelta.observacion = _concatenar_observacion_con_limite(
                    etapa_devuelta.observacion, 
                    observacion
                )
            
            etapa_devuelta.save(update_fields=['estado', 'observacion', 'actualizado_en'])
            
            _registrar_historial(
                solicitud=solicitud,
                usuario=user,
                accion='observacion',
                grupo_autorizador="Funcionario",
                nuevo_estado=etapa_devuelta.estado,
                estado_anterior=estado_anterior,
                observacion=observacion or 'Reenvío tras devolución',
            )
        
        # Reiniciar todas las etapas aprobadas a 'pendiente' para que el flujo vuelva a empezar
        etapas_aprobadas = solicitud.aprobaciones.exclude(estado__in=('devuelta', 'rechazada', 'pendiente'))
        for etapa_aprobada in etapas_aprobadas:
            etapa_aprobada.estado = 'pendiente'
            etapa_aprobada.observacion = ''
            etapa_aprobada.actualizado_por = None
            etapa_aprobada.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])
    else:
        etapas_aprobadas = solicitud.aprobaciones.filter(estado__in=('aprobada', 'autorizada'))
        if etapas_aprobadas.exists():
            for etapa_aprobada in etapas_aprobadas:
                etapa_aprobada.estado = 'pendiente'
                etapa_aprobada.observacion = ''
                etapa_aprobada.actualizado_por = None
                etapa_aprobada.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])
        
        etapa_activa = solicitud.etapa_activa
        if not etapa_activa:
            raise ValidationError("No hay etapa activa para enviar la solicitud.")
        
        _registrar_historial(
            solicitud=solicitud,
            usuario=user,
            accion='observacion',
            grupo_autorizador="Funcionario",
            nuevo_estado='pendiente',
            estado_anterior='pendiente',
            observacion=observacion or 'Primer envío al Jefe Inmediato',
        )
        etapa = None

    solicitud.estado_solicitud = 'en_revision'
    solicitud.save(update_fields=['estado_solicitud'])

    return etapa
