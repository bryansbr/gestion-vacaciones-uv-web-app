from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('vacaciones', '0017_backfill_aprobacionetapa_gfk'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aprobacionetapa',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='aprobacionetapa',
            name='object_id',
            field=models.PositiveIntegerField(),
        ),
    ]
