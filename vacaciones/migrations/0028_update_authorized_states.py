# Generated migration to update existing authorized requests/reintegros

from django.db import migrations


def update_authorized_states(apps, schema_editor):
    """
    Actualiza los estados de solicitudes y reintegros que fueron autorizados por RRHH
    para que muestren 'autorizada' en lugar de 'aprobado' o 'completado'.
    """
    SolicitudVacaciones = apps.get_model('vacaciones', 'SolicitudVacaciones')
    ReintegroVacaciones = apps.get_model('vacaciones', 'ReintegroVacaciones')
    AprobacionEtapa = apps.get_model('vacaciones', 'AprobacionEtapa')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    try:
        ct_solicitud = ContentType.objects.get(app_label='vacaciones', model='solicitudvacaciones')
    except ContentType.DoesNotExist:
        return
    
    try:
        ct_reintegro = ContentType.objects.get(app_label='vacaciones', model='reintegrovacaciones')
    except ContentType.DoesNotExist:
        ct_reintegro = None
    
    solicitudes_con_rrhh_autorizada = AprobacionEtapa.objects.filter(
        content_type=ct_solicitud,
        etapa='RRHH',
        estado='autorizada'
    ).values_list('object_id', flat=True).distinct()
    
    SolicitudVacaciones.objects.filter(
        id__in=solicitudes_con_rrhh_autorizada,
        estado_solicitud='aprobado'
    ).update(estado_solicitud='autorizada')
    
    if ct_reintegro:
        reintegros_con_rrhh_autorizada = AprobacionEtapa.objects.filter(
            content_type=ct_reintegro,
            etapa='RRHH',
            estado='autorizada'
        ).values_list('object_id', flat=True).distinct()
        
        ReintegroVacaciones.objects.filter(
            id__in=reintegros_con_rrhh_autorizada,
            estado_solicitud='completado'
        ).update(estado_solicitud='autorizada')


def reverse_update_authorized_states(apps, schema_editor):
    """
    Reversa la migración: convierte 'autorizada' de vuelta a 'aprobado' o 'completado'.
    """
    SolicitudVacaciones = apps.get_model('vacaciones', 'SolicitudVacaciones')
    ReintegroVacaciones = apps.get_model('vacaciones', 'ReintegroVacaciones')
    AprobacionEtapa = apps.get_model('vacaciones', 'AprobacionEtapa')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    try:
        ct_solicitud = ContentType.objects.get(app_label='vacaciones', model='solicitudvacaciones')
    except ContentType.DoesNotExist:
        return
    
    try:
        ct_reintegro = ContentType.objects.get(app_label='vacaciones', model='reintegrovacaciones')
    except ContentType.DoesNotExist:
        ct_reintegro = None
    
    solicitudes_con_rrhh_autorizada = AprobacionEtapa.objects.filter(
        content_type=ct_solicitud,
        etapa='RRHH',
        estado='autorizada'
    ).values_list('object_id', flat=True).distinct()
    
    SolicitudVacaciones.objects.filter(
        id__in=solicitudes_con_rrhh_autorizada,
        estado_solicitud='autorizada'
    ).update(estado_solicitud='aprobado')
    
    if ct_reintegro:
        reintegros_con_rrhh_autorizada = AprobacionEtapa.objects.filter(
            content_type=ct_reintegro,
            etapa='RRHH',
            estado='autorizada'
        ).values_list('object_id', flat=True).distinct()
        
        ReintegroVacaciones.objects.filter(
            id__in=reintegros_con_rrhh_autorizada,
            estado_solicitud='autorizada'
        ).update(estado_solicitud='completado')


class Migration(migrations.Migration):

    dependencies = [
        ('vacaciones', '0027_solicitudvacaciones_es_por_reintegro_anticipado_and_more'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(
            update_authorized_states,
            reverse_update_authorized_states
        ),
    ]
