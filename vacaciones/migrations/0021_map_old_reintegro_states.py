from django.db import migrations

def map_states(apps, schema_editor):
    Reintegro = apps.get_model('vacaciones', 'ReintegroVacaciones')
    mapping = {
        'pendiente': 'BORRADOR',
        'en_revision': 'PEND_JEFE',
        'aprobado': 'AUTORIZADA',
        'rechazado': 'RECHAZADA',
        'cancelado': 'DEVUELTA',
    }
    for old, new in mapping.items():
        Reintegro.objects.filter(estado=old).update(estado=new)

class Migration(migrations.Migration):
    dependencies = [('vacaciones','0020_alter_solicitudvacaciones_options_and_more')]
    operations = [migrations.RunPython(map_states, reverse_code=migrations.RunPython.noop)]
