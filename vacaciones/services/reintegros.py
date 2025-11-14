import logging
from typing import Optional

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from notificaciones.models import Notificacion
from usuarios.models import CustomUser
from ..models import AprobacionEtapa, ReintegroVacaciones, HistoricoAcciones

logger = logging.getLogger(__name__)

ETAPA_HUMANA = {
    'JEFE': 'Jefe Inmediato',
    'COORD': 'Coordinación Administrativa',
    'RRHH': 'División de Recursos Humanos',
}

ESTADO_GLOBAL_MAP = {
    'autorizada': 'completado',
    'rechazada': 'rechazado',
    'devuelta': 'pendiente',
    'en_progreso': 'en_revision',
    'desconocido': 'en_revision',
}

def _validar_permiso_etapa(user: CustomUser, etapa: str):
    if etapa == 'JEFE' and not (
        user.has_perm('vacaciones.dar_visto_bueno_reintegro') or
        user.groups.filter(name__in=['Jefe Inmediato', 'JEFE_INMEDIATO']).exists()
    ):
        raise PermissionDenied("No tienes permisos para aprobar/devolver como Jefe Inmediato.")

    if etapa == 'COORD' and not (
        user.has_perm('vacaciones.dar_visto_bueno_reintegro') or
        user.groups.filter(name__in=['Coordinador Administrativo', 'COORD_ADMIN']).exists()
    ):
        raise PermissionDenied("No tienes permisos para aprobar/devolver como Coordinación Administrativa.")

    if etapa == 'RRHH':
        tiene_permiso = (
            user.has_perm('vacaciones.autorizar_reintegro') or
            user.has_perm('vacaciones.rechazar_reintegro') or
            user.groups.filter(name='Recursos Humanos').exists() or
            (hasattr(user, 'email') and user.email and 'recursos.humanos' in user.email.lower())
        )
        if not tiene_permiso:
            raise PermissionDenied("No tienes permisos para autorizar/rechazar reintegros como RRHH.")

def _refrescar_estado(reintegro: ReintegroVacaciones):
    global_derivado = reintegro.estado_global
    reintegro.estado_solicitud = ESTADO_GLOBAL_MAP.get(global_derivado, 'en_revision')
    reintegro.save(update_fields=['estado_solicitud'])

def _registrar_historial(*, reintegro: ReintegroVacaciones, usuario: CustomUser, accion: str,
                         grupo_autorizador: str, nuevo_estado: str, estado_anterior: str,
                         observacion: Optional[str] = None):
    HistoricoAcciones.objects.create(
        accion_realizada=accion,
        tipo_accion='reintegro',
        usuario=usuario,
        reintegro_vacaciones=reintegro,
        grupo_autorizador=grupo_autorizador,
        nuevo_estado=nuevo_estado,
        estado_anterior=estado_anterior,
        observacion=observacion or '',
    )

def _notificar(reintegro: ReintegroVacaciones, *, destinatario, asunto: str, mensaje: str, cc=None):
    try:
        Notificacion.objects.create(
            asunto=asunto,
            mensaje=mensaje,
            funcionario=destinatario,
            funcionario_cc=cc,
            reintegro_vacaciones=reintegro,
            tipo_notificacion='reintegro',
        )
    except Exception as exc:  # pragma: no cover - logging de fallos
        logger.exception("No se pudo crear la notificación para el reintegro %s: %s", reintegro.pk, exc)

def _crear_mensaje_estado(reintegro: ReintegroVacaciones, comentario: Optional[str] = None) -> str:
    periodo = f"{reintegro.fecha_disfrute_desde.strftime('%d/%m/%Y')} - {reintegro.fecha_disfrute_hasta.strftime('%d/%m/%Y')}"
    base = (
        f"Reintegro {reintegro.codigo_sabs} del funcionario {reintegro.funcionario} por el periodo {periodo}."
    )
    if comentario:
        base = f"{base}\n\nObservaciones: {comentario.strip()}"
    return base

@transaction.atomic
def firmar_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones):
    if reintegro.funcionario.user_id != usuario.id:
        raise PermissionDenied("Solo el funcionario puede firmar su reintegro.")

    if reintegro.firmado_por_id:
        raise ValidationError("El reintegro ya fue firmado.")

    reintegro.firmado_por = usuario
    reintegro.firmado_en = timezone.now()
    reintegro.save(update_fields=['firmado_por', 'firmado_en'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='creacion' if reintegro.estado_solicitud == 'pendiente' else 'edicion',
        grupo_autorizador='Funcionario',
        nuevo_estado=reintegro.estado_solicitud,
        estado_anterior=reintegro.estado_solicitud,
        observacion='Firmado digitalmente por el funcionario',
    )
    return reintegro

@transaction.atomic
def reenviar_funcionario_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones, observacion: Optional[str] = None):
    puede_reenviar = (
        reintegro.funcionario.user_id == usuario.id or
        (reintegro.creada_por_id and reintegro.creada_por_id == usuario.id) or
        usuario.is_superuser
    )
    
    if not puede_reenviar:
        raise PermissionDenied("No tiene permisos para enviar este reintegro.")

    if reintegro.estado_solicitud not in ('pendiente',) and reintegro.estado_global != 'devuelta':
        raise ValidationError("Solo se pueden enviar reintegros pendientes o devueltos.")

    devueltas = reintegro.aprobaciones.filter(estado='devuelta', etapa__in=('JEFE', 'COORD'))
    if devueltas.exists():
        for etapa in devueltas:
            estado_anterior = etapa.estado
            etapa.estado = 'pendiente'
            etapa.observacion = ''
            etapa.actualizado_por = None
            etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

            _registrar_historial(
                reintegro=reintegro,
                usuario=usuario,
                accion='observacion',
                grupo_autorizador='Funcionario',
                nuevo_estado=etapa.estado,
                estado_anterior=estado_anterior,
                observacion=observacion or 'Reenvío tras devolución',
            )
    else:
        if reintegro.aprobaciones.count() == 0:
            ct_reintegro = ContentType.objects.get_for_model(ReintegroVacaciones)
            solicitud_fk = getattr(reintegro, 'solicitud_vacaciones', None)
            AprobacionEtapa.objects.bulk_create([
                AprobacionEtapa(
                    content_type=ct_reintegro,
                    object_id=reintegro.pk,
                    solicitud=solicitud_fk,
                    etapa='JEFE',
                    estado='pendiente'
                ),
                AprobacionEtapa(
                    content_type=ct_reintegro,
                    object_id=reintegro.pk,
                    solicitud=solicitud_fk,
                    etapa='COORD',
                    estado='pendiente'
                ),
                AprobacionEtapa(
                    content_type=ct_reintegro,
                    object_id=reintegro.pk,
                    solicitud=solicitud_fk,
                    etapa='RRHH',
                    estado='pendiente'
                ),
            ])
        else:
            for etapa in reintegro.aprobaciones.filter(estado__in=('aprobada', 'autorizada')):
                etapa.estado = 'pendiente'
                etapa.observacion = ''
                etapa.actualizado_por = None
                etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    reintegro.estado_solicitud = 'en_revision'
    reintegro.save(update_fields=['estado_solicitud'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='observacion',
        grupo_autorizador='Funcionario',
        nuevo_estado='en_revision',
        estado_anterior='pendiente',
        observacion=observacion or 'Enviado al Jefe Inmediato',
    )

    funcionario = reintegro.funcionario
    jefe = funcionario.jefe_inmediato
    if jefe:
        _notificar(
            reintegro,
            destinatario=jefe,
            asunto=f"Nuevo reintegro {reintegro.codigo_sabs} pendiente",
            mensaje=_crear_mensaje_estado(reintegro, observacion),
            cc=funcionario,
        )
    return reintegro

@transaction.atomic
def aprobar_etapa_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones, observacion: Optional[str] = None):
    etapa = reintegro.etapa_activa
    if not etapa:
        raise ValidationError("No hay etapa activa para aprobar.")
    if etapa.etapa not in ('JEFE', 'COORD'):
        raise ValidationError("Solo Jefe Inmediato o Coordinación pueden aprobar etapas intermedias.")

    _validar_permiso_etapa(usuario, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'aprobada'
    etapa.observacion = observacion or ''
    etapa.actualizado_por = usuario
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='aprobacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    _refrescar_estado(reintegro)

    funcionario = reintegro.funcionario
    if etapa.etapa == 'JEFE':
        mensaje = _crear_mensaje_estado(reintegro, observacion)
        _notificar(
            reintegro,
            destinatario=funcionario,
            asunto=f"Reintegro {reintegro.codigo_sabs} aprobado por Jefe Inmediato",
            mensaje=mensaje,
        )
    elif etapa.etapa == 'COORD':
        mensaje = _crear_mensaje_estado(reintegro, observacion)
        _notificar(
            reintegro,
            destinatario=funcionario,
            asunto=f"Reintegro {reintegro.codigo_sabs} aprobado por Coordinación Administrativa",
            mensaje=mensaje,
        )
        
        try:
            grupo_rrhh = Group.objects.get(name='Recursos Humanos')
            usuarios_rrhh = grupo_rrhh.user_set.filter(is_active=True)
            
            for usuario_rrhh in usuarios_rrhh:
                rrhh_func = getattr(usuario_rrhh, 'funcionario', None)
                if rrhh_func:
                    mensaje_rrhh = (
                        f"El reintegro {reintegro.codigo_sabs} del funcionario {funcionario} "
                        f"ha sido aprobado por Coordinación Administrativa y está pendiente de su revisión.\n\n"
                        f"{mensaje}"
                    )
                    _notificar(
                        reintegro,
                        destinatario=rrhh_func,
                        asunto=f"Reintegro {reintegro.codigo_sabs} pendiente de autorización",
                        mensaje=mensaje_rrhh,
                        cc=funcionario,
                    )
        except Group.DoesNotExist:
            logger.warning("No se encontró el grupo 'Recursos Humanos' para notificar.")
        except Exception as exc:
            logger.exception("Error al notificar a RRHH sobre reintegro aprobado por COORD: %s", exc)
    
    return etapa

@transaction.atomic
def devolver_etapa_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones, observacion: str):
    if not observacion or not observacion.strip():
        raise ValidationError("Debe indicar el motivo de la devolución.")

    etapa = reintegro.etapa_activa
    if not etapa or etapa.etapa not in ('JEFE', 'COORD'):
        raise ValidationError("Solo Jefe Inmediato o Coordinación pueden devolver.")

    _validar_permiso_etapa(usuario, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa no está pendiente para devolución.")

    estado_anterior = etapa.estado
    etapa.estado = 'devuelta'
    etapa.observacion = observacion.strip()
    etapa.actualizado_por = usuario
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    for etapa_a_reiniciar in reintegro.aprobaciones.exclude(pk=etapa.pk):
        etapa_a_reiniciar.estado = 'pendiente'
        etapa_a_reiniciar.observacion = ''
        etapa_a_reiniciar.actualizado_por = None
        etapa_a_reiniciar.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    reintegro.estado_solicitud = 'pendiente'
    reintegro.save(update_fields=['estado_solicitud'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='observacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    funcionario = reintegro.funcionario
    _notificar(
        reintegro,
        destinatario=funcionario,
        asunto=f"Reintegro {reintegro.codigo_sabs} devuelto",
        mensaje=_crear_mensaje_estado(reintegro, observacion),
    )
    return etapa

@transaction.atomic
def autorizar_rrhh_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones, observacion: Optional[str] = None):
    etapa = reintegro.etapa_activa
    if not etapa or etapa.etapa != 'RRHH':
        raise ValidationError("Solo RRHH puede autorizar en la etapa correspondiente.")

    _validar_permiso_etapa(usuario, etapa.etapa)

    req = {a.etapa: a.estado for a in reintegro.aprobaciones.all()}
    if not (req.get('JEFE') == 'aprobada' and req.get('COORD') == 'aprobada'):
        raise ValidationError("No se puede autorizar: JEFE y COORD deben aprobar primero.")

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa de RRHH no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'autorizada'
    etapa.observacion = observacion or ''
    etapa.actualizado_por = usuario
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    reintegro.estado_solicitud = 'completado'
    reintegro.save(update_fields=['estado_solicitud'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='aprobacion',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    funcionario = reintegro.funcionario
    _notificar(
        reintegro,
        destinatario=funcionario,
        asunto=f"Reintegro {reintegro.codigo_sabs} autorizado",
        mensaje=_crear_mensaje_estado(reintegro, observacion),
    )
    return etapa

@transaction.atomic
def rechazar_rrhh_reintegro(usuario: CustomUser, reintegro: ReintegroVacaciones, observacion: str):
    if not observacion or not observacion.strip():
        raise ValidationError("Debe indicar el motivo del rechazo.")

    etapa = reintegro.etapa_activa
    if not etapa or etapa.etapa != 'RRHH':
        raise ValidationError("Solo RRHH puede rechazar en la etapa correspondiente.")

    _validar_permiso_etapa(usuario, etapa.etapa)

    if etapa.estado != 'pendiente':
        raise ValidationError("La etapa de RRHH no está pendiente.")

    estado_anterior = etapa.estado
    etapa.estado = 'rechazada'
    etapa.observacion = observacion.strip()
    etapa.actualizado_por = usuario
    etapa.save(update_fields=['estado', 'observacion', 'actualizado_por', 'actualizado_en'])

    reintegro.estado_solicitud = 'rechazado'
    reintegro.save(update_fields=['estado_solicitud'])

    _registrar_historial(
        reintegro=reintegro,
        usuario=usuario,
        accion='rechazo',
        grupo_autorizador=ETAPA_HUMANA[etapa.etapa],
        nuevo_estado=etapa.estado,
        estado_anterior=estado_anterior,
        observacion=observacion,
    )

    funcionario = reintegro.funcionario
    jefe = funcionario.jefe_inmediato
    _notificar(
        reintegro,
        destinatario=funcionario,
        asunto=f"Reintegro {reintegro.codigo_sabs} rechazado",
        mensaje=_crear_mensaje_estado(reintegro, observacion),
    )
    if jefe:
        _notificar(
            reintegro,
            destinatario=jefe,
            asunto=f"Reintegro {reintegro.codigo_sabs} rechazado",
            mensaje=_crear_mensaje_estado(reintegro, observacion),
            cc=funcionario,
        )
    return etapa
