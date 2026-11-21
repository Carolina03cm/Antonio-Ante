from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def fecha_seguimiento_predeterminada():
    return timezone.now() + timedelta(days=1)

class NoticiaComunicado(models.Model):
    """
    Modelo para noticias, comunicados oficiales y avisos escolares.
    """
    TIPO_CHOICES = [
        ('comunicado', 'Comunicado Oficial'),
        ('noticia', 'Noticia Institucional'),
        ('urgente', 'Aviso Importante'),
        ('dece', 'Aviso DECE'),
    ]

    titulo = models.CharField('Título', max_length=200)
    tipo = models.CharField('Tipo de Publicación', max_length=20, choices=TIPO_CHOICES, default='noticia')
    resumen = models.CharField('Resumen breve', max_length=300, help_text='Texto descriptivo para la portada.')
    contenido = models.TextField('Contenido completo')
    imagen = models.ImageField('Fotografía adjunta', upload_to='noticias/', blank=True, null=True, max_length=500)
    destacado = models.BooleanField('Mostrar en portada', default=True)
    fecha_publicacion = models.DateTimeField('Fecha de publicación', auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Autor')

    class Meta:
        verbose_name = 'Noticia y Comunicado'
        verbose_name_plural = 'Noticias y Comunicados'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"


class FotoGaleria(models.Model):
    """
    Modelo para fotografías de actividades y vida escolar.
    """
    CATEGORIA_CHOICES = [
        ('civico', 'Momento Cívico'),
        ('deportes', 'Juegos Escolares'),
        ('ciencias', 'Feria Científica y Arte'),
        ('lectura', 'Club de Lectura y Biblioteca'),
        ('institucional', 'Vida Institucional'),
    ]

    titulo = models.CharField('Título de la actividad', max_length=150)
    categoria = models.CharField('Categoría', max_length=30, choices=CATEGORIA_CHOICES, default='institucional')
    imagen = models.ImageField('Fotografía', upload_to='galeria/', max_length=500)
    descripcion = models.CharField('Subtítulo o descripción', max_length=250, blank=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True)
    activa = models.BooleanField('Visible en la web', default=True)

    class Meta:
        verbose_name = 'Fotografía de Galería'
        verbose_name_plural = 'Fotografías de Galería'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"


class DocentePersonal(models.Model):
    """
    Modelo para la nómina de docentes divididos en Jornada Matutina, Vespertina y DECE.
    """
    JORNADA_CHOICES = [
        ('autoridades', 'Autoridades Institucionales'),
        ('matutina', 'Jornada Matutina'),
        ('vespertina', 'Jornada Vespertina'),
        ('dece', 'Departamento DECE'),
    ]
    FUNCION_CHOICES = [
        ('docente', 'Docente'),
        ('tutor', 'Tutor/a de curso'),
        ('autoridad', 'Autoridad institucional'),
        ('rector', 'Rector/a'),
        ('vicerrector', 'Vicerrector/a'),
        ('director', 'Director/a'),
        ('inspector', 'Inspector/a general'),
        ('subinspector', 'Subinspector/a'),
        ('secretaria', 'Secretario/a'),
        ('coordinador', 'Coordinador/a'),
        ('dece', 'Personal DECE'),
        ('otro', 'Otro cargo'),
    ]
    FUNCIONES_AUTORIDAD = {
        'autoridad', 'rector', 'vicerrector', 'director', 'inspector',
        'subinspector', 'secretaria', 'coordinador'
    }

    nombres = models.CharField('Nombres', max_length=100)
    apellidos = models.CharField('Apellidos', max_length=100)
    cargo = models.CharField('Detalle del cargo o curso', max_length=150, blank=True, help_text='Ej: Tutor de 4to EGB')
    jornada = models.CharField('Jornada / Área', max_length=20, choices=JORNADA_CHOICES, default='matutina')
    area = models.CharField('Especialidad o Asignatura', max_length=120, blank=True, help_text='Ej: Lengua y Literatura, Ciencias Naturales')
    funciones = models.JSONField('Funciones y cargos', default=list, blank=True)
    jornadas = models.JSONField('Jornadas asignadas', default=list, blank=True)
    asignaturas = models.JSONField('Materias o asignaturas', default=list, blank=True)
    foto = models.ImageField('Fotografía del Docente', upload_to='docentes/', blank=True, null=True, max_length=500)
    orden = models.PositiveIntegerField('Orden de visualización', default=1)
    activo = models.BooleanField('Activo en nómina', default=True)

    class Meta:
        verbose_name = 'Docente / Personal'
        verbose_name_plural = 'Planta Docente y Personal'
        ordering = ['jornada', 'orden', 'apellidos']

    def __str__(self):
        return f"{self.apellidos} {self.nombres} - {self.cargo} ({self.get_jornada_display()})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def funciones_asignadas(self):
        if self.funciones:
            return self.funciones
        cargo = (self.cargo or '').casefold()
        funciones = []
        if 'docent' in cargo or self.jornada in ('matutina', 'vespertina'):
            funciones.append('docente')
        if 'tutor' in cargo:
            funciones.append('tutor')
        if self.jornada == 'autoridades':
            funciones.append('autoridad')
        if self.jornada == 'dece' or 'dece' in cargo or 'psicolog' in cargo:
            funciones.append('dece')
        if 'vicerrector' in cargo:
            funciones.append('vicerrector')
        elif 'rector' in cargo:
            funciones.append('rector')
        if 'subinspector' in cargo:
            funciones.append('subinspector')
        elif 'inspector' in cargo:
            funciones.append('inspector')
        if 'secretar' in cargo:
            funciones.append('secretaria')
        if 'director' in cargo:
            funciones.append('director')
        if 'coordinador' in cargo:
            funciones.append('coordinador')
        return funciones or ['otro']

    @property
    def jornadas_asignadas(self):
        return self.jornadas or [self.jornada]

    @property
    def funciones_display(self):
        etiquetas = dict(self.FUNCION_CHOICES)
        return [etiquetas.get(funcion, funcion) for funcion in self.funciones_asignadas]

    @property
    def jornadas_display(self):
        etiquetas = dict(self.JORNADA_CHOICES)
        return [etiquetas.get(jornada, jornada) for jornada in self.jornadas_asignadas]

    @property
    def asignaturas_display(self):
        if self.asignaturas:
            return self.asignaturas
        return [materia.strip() for materia in self.area.replace(';', ',').split(',') if materia.strip()]

    @property
    def es_autoridad(self):
        return self.jornada == 'autoridades' or any(
            funcion in self.FUNCIONES_AUTORIDAD for funcion in self.funciones_asignadas
        )

    @property
    def esta_en_dece(self):
        return 'dece' in self.jornadas_asignadas or 'dece' in self.funciones_asignadas


class MensajeContacto(models.Model):
    """
    Registro de consultas enviadas desde el formulario web de secretaría.
    """
    PRIORIDAD_CHOICES = [
        (1, 'Urgente'),
        (2, 'Alta'),
        (3, 'Normal'),
        (4, 'Baja'),
    ]
    NIVEL_INTERES_CHOICES = [
        ('inicial', 'Educación Inicial'),
        ('1_egb', '1.º de EGB'),
        ('2_egb', '2.º de EGB'),
        ('3_egb', '3.º de EGB'),
        ('4_egb', '4.º de EGB'),
        ('5_egb', '5.º de EGB'),
        ('6_egb', '6.º de EGB'),
        ('7_egb', '7.º de EGB'),
        ('8_egb', '8.º de EGB'),
        ('9_egb', '9.º de EGB'),
        ('10_egb', '10.º de EGB'),
    ]

    nombre = models.CharField('Nombre del Representante', max_length=150)
    telefono = models.CharField('Teléfono / WhatsApp', max_length=25)
    email = models.EmailField('Correo electrónico', blank=True)
    nivel_interes = models.CharField('Nivel educativo de interés', max_length=10, blank=True, choices=NIVEL_INTERES_CHOICES)
    mensaje = models.TextField('Consulta o Trámite', blank=True)
    acepta_privacidad = models.BooleanField('Acepta el uso de datos para responder', default=False)
    fecha_envio = models.DateTimeField('Fecha de recepción', auto_now_add=True)
    leido = models.BooleanField('Atendido', default=False)
    prioridad = models.PositiveSmallIntegerField('Prioridad', choices=PRIORIDAD_CHOICES, default=3)
    fecha_seguimiento = models.DateTimeField(
        'Recordatorio de seguimiento', default=fecha_seguimiento_predeterminada
    )

    class Meta:
        verbose_name = 'Consulta de Secretaría'
        verbose_name_plural = 'Consultas de Secretaría'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Consulta de {self.nombre} ({self.telefono})"

    @property
    def necesita_recordatorio(self):
        return not self.leido and self.fecha_seguimiento <= timezone.now()

    @property
    def telefono_whatsapp(self):
        digitos = ''.join(caracter for caracter in self.telefono if caracter.isdigit())
        if digitos.startswith('0'):
            digitos = digitos[1:]
        if not digitos.startswith('593'):
            digitos = f'593{digitos}'
        return digitos


class PerfilUsuario(models.Model):
    """
    Extensión del usuario institucional con Cédula, Nombres, Apellidos, Rol Escolar y Foto.
    """
    ROLES_CHOICES = [
        ('administrador', 'Administrador General'),
        ('noticias', 'Editor de Noticias y Comunicados'),
        ('galeria', 'Gestor de Galería Fotográfica'),
        ('docente', 'Docente / Personal Institucional'),
        ('dece', 'Consejero DECE'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cedula = models.CharField('Número de Cédula', max_length=15, blank=True)
    nombres = models.CharField('Nombres', max_length=100, blank=True)
    apellidos = models.CharField('Apellidos', max_length=100, blank=True)
    rol = models.CharField('Rol Asignado', max_length=30, choices=ROLES_CHOICES, default='docente')
    foto = models.ImageField('Foto de Perfil', upload_to='perfiles/', blank=True, null=True, max_length=500)
    debe_cambiar_password = models.BooleanField('Debe cambiar contraseña al iniciar', default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_rol_display()})"

    @property
    def nombre_completo(self):
        if self.nombres or self.apellidos:
            return f"{self.nombres} {self.apellidos}".strip()
        full = self.user.get_full_name()
        return full if full else self.user.username

    @property
    def iniciales(self):
        n = self.nombres or self.user.first_name or self.user.username
        a = self.apellidos or self.user.last_name or ''
        ini_n = n[0] if n else ''
        ini_a = a[0] if a else (self.user.username[1] if len(self.user.username) > 1 else '')
        return f"{ini_n}{ini_a}".upper()


class CifrasInstitucionales(models.Model):
    """Dato de matrícula que se actualiza desde el administrador institucional."""
    total_estudiantes = models.PositiveIntegerField(
        'Total de estudiantes matriculados', blank=True, null=True,
        help_text='Actualiza esta cifra cuando cambie la matrícula institucional.',
    )

    class Meta:
        verbose_name = 'Cifra institucional'
        verbose_name_plural = 'Cifras institucionales'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Datos públicos de matrícula'


class OfertaAcademica(models.Model):
    """Fotografia editable para cada nivel de la oferta academica."""
    NIVELES = [
        ('inicial', 'Educacion Inicial'),
        ('elemental', 'Basica Elemental'),
        ('media', 'Basica Media'),
        ('superior', 'Basica Superior'),
    ]
    nivel = models.CharField('Nivel', max_length=20, choices=NIVELES, unique=True)
    imagen = models.ImageField('Fotografia', upload_to='oferta_academica/', max_length=500)
    actualizada = models.DateTimeField('Ultima actualizacion', auto_now=True)

    class Meta:
        verbose_name = 'Fotografia de oferta academica'
        verbose_name_plural = 'Fotografias de oferta academica'
        ordering = ('nivel',)

    def __str__(self):
        return self.get_nivel_display()