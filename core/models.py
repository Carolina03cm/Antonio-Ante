from django.db import models
from django.contrib.auth.models import User

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
    imagen = models.ImageField('Fotografía adjunta', upload_to='noticias/', blank=True, null=True)
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
    imagen = models.ImageField('Fotografía', upload_to='galeria/')
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

    nombres = models.CharField('Nombres', max_length=100)
    apellidos = models.CharField('Apellidos', max_length=100)
    cargo = models.CharField('Cargo o Rol', max_length=150, help_text='Ej: Docente Tutor 3° EGB, Psicólogo Educativo')
    jornada = models.CharField('Jornada / Área', max_length=20, choices=JORNADA_CHOICES, default='matutina')
    area = models.CharField('Especialidad o Asignatura', max_length=120, blank=True, help_text='Ej: Lengua y Literatura, Ciencias Naturales')
    foto = models.ImageField('Fotografía del Docente', upload_to='docentes/', blank=True, null=True)
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


class MensajeContacto(models.Model):
    """
    Registro de consultas enviadas desde el formulario web de secretaría.
    """
    nombre = models.CharField('Nombre del Representante', max_length=150)
    telefono = models.CharField('Teléfono / WhatsApp', max_length=25)
    mensaje = models.TextField('Consulta o Trámite')
    fecha_envio = models.DateTimeField('Fecha de recepción', auto_now_add=True)
    leido = models.BooleanField('Atendido', default=False)

    class Meta:
        verbose_name = 'Consulta de Secretaría'
        verbose_name_plural = 'Consultas de Secretaría'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Consulta de {self.nombre} ({self.telefono})"
