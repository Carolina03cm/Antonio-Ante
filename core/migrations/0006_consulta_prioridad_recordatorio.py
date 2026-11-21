from datetime import timedelta

import core.models
from django.db import migrations, models
from django.utils import timezone


def inicializar_seguimientos(apps, schema_editor):
    MensajeContacto = apps.get_model('core', 'MensajeContacto')
    for consulta in MensajeContacto.objects.all().iterator():
        consulta.fecha_seguimiento = consulta.fecha_envio + timedelta(days=1)
        consulta.save(update_fields=['fecha_seguimiento'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_docente_asignaciones_multiples'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensajecontacto',
            name='prioridad',
            field=models.PositiveSmallIntegerField(
                choices=[(1, 'Urgente'), (2, 'Alta'), (3, 'Normal'), (4, 'Baja')],
                default=3,
                verbose_name='Prioridad',
            ),
        ),
        migrations.AddField(
            model_name='mensajecontacto',
            name='fecha_seguimiento',
            field=models.DateTimeField(
                default=core.models.fecha_seguimiento_predeterminada,
                verbose_name='Recordatorio de seguimiento',
            ),
        ),
        migrations.RunPython(inicializar_seguimientos, migrations.RunPython.noop),
    ]
