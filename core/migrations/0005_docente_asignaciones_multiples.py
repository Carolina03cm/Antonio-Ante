import re

from django.db import migrations, models


def migrar_asignaciones_docentes(apps, schema_editor):
    DocentePersonal = apps.get_model('core', 'DocentePersonal')
    for docente in DocentePersonal.objects.all().iterator():
        cargo = (docente.cargo or '').casefold()
        funciones = []

        if docente.jornada == 'autoridades':
            funciones.append('autoridad')
        if docente.jornada in ('matutina', 'vespertina') or 'docent' in cargo:
            funciones.append('docente')
        if 'tutor' in cargo:
            funciones.append('tutor')
        if 'rector' in cargo:
            funciones.append('vicerrector' if 'vice' in cargo else 'rector')
        elif 'director' in cargo:
            funciones.append('director')
        if 'inspector' in cargo:
            funciones.append('subinspector' if 'sub' in cargo else 'inspector')
        if 'secretar' in cargo:
            funciones.append('secretaria')
        if 'coordinador' in cargo:
            funciones.append('coordinador')
        if docente.jornada == 'dece' or 'dece' in cargo or 'psicolog' in cargo:
            funciones.append('dece')
        if not funciones:
            funciones.append('otro')

        materias = [
            ' '.join(materia.split())
            for materia in re.split(r'[,;\n]+', docente.area or '')
            if materia.strip()
        ]
        docente.funciones = list(dict.fromkeys(funciones))
        docente.jornadas = [docente.jornada] if docente.jornada else []
        docente.asignaturas = materias
        docente.save(update_fields=['funciones', 'jornadas', 'asignaturas'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_perfil_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='docentepersonal',
            name='cargo',
            field=models.CharField(blank=True, help_text='Ej: Tutor de 4to EGB', max_length=150, verbose_name='Detalle del cargo o curso'),
        ),
        migrations.AddField(
            model_name='docentepersonal',
            name='funciones',
            field=models.JSONField(blank=True, default=list, verbose_name='Funciones y cargos'),
        ),
        migrations.AddField(
            model_name='docentepersonal',
            name='jornadas',
            field=models.JSONField(blank=True, default=list, verbose_name='Jornadas asignadas'),
        ),
        migrations.AddField(
            model_name='docentepersonal',
            name='asignaturas',
            field=models.JSONField(blank=True, default=list, verbose_name='Materias o asignaturas'),
        ),
        migrations.RunPython(migrar_asignaciones_docentes, migrations.RunPython.noop),
    ]
