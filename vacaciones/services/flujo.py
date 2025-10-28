from django.utils import timezone
from django.apps import apps
from vacaciones.models import HistoricoAcciones

PENDIENTE_JEFE   = "PENDIENTE_JEFE"
PENDIENTE_COORD  = "PENDIENTE_COORD"
DEVUELTA_JEFE    = "DEVUELTA_JEFE"
APROBADA_FINAL   = "APROBADA_FINAL"

def _Notificacion():
    return apps.get_model("notificaciones", "Notificacion")

def _registrar_historial(solicitud, user, accion, nuevo_estado, comentario="", grupo="JEFE_INMEDIATO"):
    HistoricoAcciones.objects.create(
        solicitud=solicitud,
        actor=user,
        grupo_autorizador=grupo,
        accion_realizada=accion,
        comentario=comentario,
        nuevo_estado=nuevo_estado,
        timestamp=timezone.now(),
    )

def _notificar_solicitud(destinatario_funcionario, asunto, mensaje, solicitud, cc_funcionario=None):
    Notificacion = _Notificacion()
    Notificacion.objects.create(
        asunto=asunto,
        mensaje=mensaje,
        funcionario=destinatario_funcionario,
        funcionario_cc=cc_funcionario,
        solicitud_vacaciones=solicitud,
        tipo_notificacion="solicitud",
    )

def transicion_aprobar_por_jefe(solicitud, user, comentario=""):
    if solicitud.estado_solicitud != PENDIENTE_JEFE:
        return False, "La solicitud no está pendiente del Jefe Inmediato."

    solicitud.estado_solicitud = PENDIENTE_COORD
    solicitud.save(update_fields=["estado_solicitud"])

    _registrar_historial(solicitud, user, "APROBAR", PENDIENTE_COORD, comentario)
    _notificar_solicitud(
        destinatario_funcionario=solicitud.funcionario,
        asunto="Solicitud aprobada por Jefe Inmediato",
        mensaje="Tu solicitud avanzó a Coordinación Administrativa.",
        solicitud=solicitud,
        cc_funcionario=None,
    )
    return True, "Solicitud aprobada y enviada a Coordinación Administrativa."

def transicion_devolver_por_jefe(solicitud, user, comentario=""):
    if solicitud.estado_solicitud != PENDIENTE_JEFE:
        return False, "La solicitud no está pendiente del Jefe Inmediato."
    if not comentario.strip():
        return False, "Debes indicar un motivo de devolución."

    solicitud.estado_solicitud = DEVUELTA_JEFE
    solicitud.save(update_fields=["estado_solicitud"])

    _registrar_historial(solicitud, user, "DEVOLVER", DEVUELTA_JEFE, comentario)
    _notificar_solicitud(
        destinatario_funcionario=solicitud.funcionario,
        asunto="Solicitud devuelta por Jefe Inmediato",
        mensaje=f"Motivo: {comentario}",
        solicitud=solicitud,
        cc_funcionario=None,
    )
    return True, "Solicitud devuelta al Funcionario."
