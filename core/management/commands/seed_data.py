from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import NoticiaComunicado, FotoGaleria, DocentePersonal

class Command(BaseCommand):
    help = 'Carga datos institucionales iniciales para la EEB Antonio Ante'

    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).first()

        # 1. Semilla de Docentes por Jornada y DECE
        docentes_data = [
            # Jornada Matutina
            ('Lcda. María', 'Guamán', 'Docente Tutora Inicial 1 y 2', 'matutina', 'Educación Inicial', 1),
            ('Prof. Jorge', 'Mendoza', 'Docente Tutor 2° y 3° EGB', 'matutina', 'Básica Elemental', 2),
            ('Lcda. Carmen', 'Alvarado', 'Docente Tutora 4° y 5° EGB', 'matutina', 'Básica Elemental y Media', 3),
            ('Prof. Luis', 'Vera', 'Docente Tutor 6° y 7° EGB', 'matutina', 'Ciencias Exactas', 4),
            ('Lcdo. Roberto', 'Castro', 'Docente 8°, 9° y 10° EGB', 'matutina', 'Lengua y Literatura', 5),
            ('Lcda. Diana', 'Paredes', 'Docente de Matemáticas', 'matutina', 'Básica Superior', 6),
            ('Prof. Carlos', 'Morán', 'Docente de Educación Física', 'matutina', 'Cultura Física y Deportes', 7),
            
            # Jornada Vespertina
            ('Lcda. Rosa', 'Sánchez', 'Docente Tutora 2° a 4° EGB', 'vespertina', 'Básica Elemental', 1),
            ('Prof. Manuel', 'Chávez', 'Docente Tutor 5° a 7° EGB', 'vespertina', 'Básica Media', 2),
            ('Lcdo. Fernando', 'Salazar', 'Docente 8° a 10° EGB', 'vespertina', 'Ciencias Naturales y Sociales', 3),
            ('Lcda. Elena', 'Romero', 'Docente de Inglés', 'vespertina', 'Lengua Extranjera', 4),
            ('Prof. Gabriel', 'Zambrano', 'Docente de Proyectos Escolares', 'vespertina', 'Arte y Tecnología', 5),

            # DECE
            ('Psic. Andrea', 'Bravo', 'Psicóloga Educativa', 'dece', 'Consejería y Bienestar Estudiantil', 1),
            ('Lcda. Patricia', 'Morales', 'Trabajadora Social', 'dece', 'Apoyo Familiar y Comunitario', 2),
        ]

        for nombres, apellidos, cargo, jornada, area, orden in docentes_data:
            DocentePersonal.objects.get_or_create(
                nombres=nombres,
                apellidos=apellidos,
                defaults={
                    'cargo': cargo,
                    'jornada': jornada,
                    'area': area,
                    'orden': orden,
                    'activo': True
                }
            )

        # 2. Semilla de Noticias y Comunicados
        noticias_data = [
            (
                'Proceso Oficial de Matrículas y Requisitos del Ciclo Lectivo',
                'comunicado',
                'Se informa a los señores padres de familia del Recinto El Deseo sobre el cronograma oficial de matrículas para las jornadas matutina y vespertina.',
                'La dirección y secretaría de la EEB Antonio Ante informa a la comunidad educativa que el proceso de matrículas ordinarias se encuentra abierto conforme al cronograma del Ministerio de Educación. Se solicita presentar copia de cédula del estudiante y del representante legal, comprobante de residencia y récord académico en las oficinas de secretaría.',
                True
            ),
            (
                'Solemne Juramento a la Bandera Nacional y Cuadro de Honor',
                'noticia',
                'Nuestros estudiantes de décimo año rindieron homenaje a los símbolos patrios en un acto cívico solemne junto a la planta docente.',
                'En un emotivo marco de fervor cívico, la comunidad educativa de la Escuela Antonio Ante celebró el Juramento a la Bandera Nacional. Se entregaron menciones de honor a los abanderados y escoltas del pabellón nacional, provincial y cantonal.',
                True
            ),
            (
                'Talleres de Convivencia Armónica y Escuela para Padres (DECE)',
                'dece',
                'El Departamento de Consejería Estudiantil convoca a los representantes para los talleres de convivencia y fortalecimiento de valores.',
                'El equipo profesional del DECE invita cordialmente a todos los padres de familia y representantes legales a participar en los ciclos de talleres formativos enfocados en pautas de crianza positiva, prevención socioemocional y acompañamiento académico en el hogar.',
                True
            )
        ]

        for titulo, tipo, resumen, contenido, destacado in noticias_data:
            NoticiaComunicado.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': tipo,
                    'resumen': resumen,
                    'contenido': contenido,
                    'destacado': destacado,
                    'autor': admin_user
                }
            )

        # 3. Semilla de Galería Fotográfica
        galeria_data = [
            ('Minuto Cívico Institucional', 'civico', 'Valores patrios y formación ciudadana en el patio central.', 'galeria_civica.jpg'),
            ('Jornadas Deportivas Escolares', 'deportes', 'Competencias atléticas y fomento del trabajo en equipo.', 'galeria_deportes.jpg'),
            ('Feria de Ciencias y Proyectos', 'ciencias', 'Demostración de proyectos creativos y experimentos escolares.', 'galeria_ciencias.jpg'),
            ('Club de Lectura y Biblioteca', 'lectura', 'Fomento del hábito lector en niños y niñas de primaria.', 'galeria_lectura.jpg'),
        ]

        for titulo, cat, desc, img_name in galeria_data:
            # Asignar archivo existente en static/img/
            FotoGaleria.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'categoria': cat,
                    'descripcion': desc,
                    'imagen': f"galeria/{img_name}",
                    'activa': True
                }
            )

        self.stdout.write(self.style.SUCCESS('¡Datos institucionales iniciales sembrados con éxito!'))
