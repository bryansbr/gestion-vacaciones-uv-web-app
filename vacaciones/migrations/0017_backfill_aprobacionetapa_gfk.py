from django.db import migrations
from django.db.models import F  # <-- añade esto

def forwards(apps, schema_editor):
    AprobacionEtapa = apps.get_model('vacaciones', 'AprobacionEtapa')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    SolicitudVacaciones = apps.get_model('vacaciones', 'SolicitudVacaciones')

    ct_sol = ContentType.objects.get_for_model(SolicitudVacaciones)

    (AprobacionEtapa.objects
        .filter(content_type__isnull=True, solicitud__isnull=False)
        .update(content_type_id=ct_sol.id, object_id=F('solicitud_id')))

def backwards(apps, schema_editor):
    AprobacionEtapa = apps.get_model('vacaciones', 'AprobacionEtapa')
    AprobacionEtapa.objects.update(content_type=None, object_id=None)

class Migration(migrations.Migration):

    dependencies = [
        ('vacaciones', '0016_alter_aprobacionetapa_unique_together_and_more'),  # deja tu dependencia previa
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
