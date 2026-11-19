from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Configura los roles y grupos de permisos oficiales de la EEB Antonio Ante'

    def handle(self, *args, **options):
        # 1. Definir los roles oficiales de la institución
        roles = [
            ('Administradores', 'Control total del sistema, usuarios y contenidos.'),
            ('Docentes', 'Publicación y edición de noticias, comunicados y fotografías.'),
            ('DECE', 'Publicación de avisos de orientación y talleres para padres.'),
        ]

        for role_name, description in roles:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol creado con éxito: {role_name}'))
            else:
                self.stdout.write(f'El rol ya existía: {role_name}')

        self.stdout.write(self.style.SUCCESS('Configuración de roles institucionales completada exitosamente.'))
