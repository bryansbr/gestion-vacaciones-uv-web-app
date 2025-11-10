from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import SolicitudVacaciones, ReintegroVacaciones, AprobacionEtapa

ETAPAS = getattr(SolicitudVacaciones, 'ETAPAS_ORDEN', ('JEFE', 'COORD', 'RRHH'))

def _crear_etapas_por_defecto(instance):
    existentes = set(AprobacionEtapa.objects.filter(
        content_type=ContentType.objects.get_for_model(instance.__class__),
        object_id=instance.pk
    ).values_list('etapa', flat=True))

    por_crear = [e for e in ETAPAS if e not in existentes]
    if not por_crear:
        return

    ct = ContentType.objects.get_for_model(instance.__class__)

    solicitud_fk = None
    if isinstance(instance, SolicitudVacaciones):
        solicitud_fk = instance
    elif isinstance(instance, ReintegroVacaciones):
        solicitud_fk = getattr(instance, 'solicitud_vacaciones', None)

    objs = [
        AprobacionEtapa(
            solicitud=solicitud_fk,
            etapa=e,
            estado='pendiente',
            content_type=ct,
            object_id=instance.pk,
        )
        for e in por_crear
    ]
    AprobacionEtapa.objects.bulk_create(objs)

@receiver(post_save, sender=SolicitudVacaciones)
def crear_etapas_solicitud(sender, instance, created, **kwargs):
    if created:
        _crear_etapas_por_defecto(instance)

@receiver(post_save, sender=ReintegroVacaciones)
def crear_etapas_reintegro(sender, instance, created, **kwargs):
    if created:
        _crear_etapas_por_defecto(instance)
