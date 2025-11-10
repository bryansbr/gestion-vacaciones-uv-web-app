from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacaciones', '0023_alter_reintegrovacaciones_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitudvacaciones',
            name='estado_solicitud',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('en_revision', 'En revisión'),
                    ('aprobado', 'Aprobada'),
                    ('rechazado', 'Rechazada'),
                    ('devuelta', 'Devuelta'),
                    ('cancelado', 'Cancelado'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]

