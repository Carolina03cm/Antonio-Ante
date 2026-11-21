import unicodedata
import re
from django import forms
from django.contrib.auth.models import User
from .models import (
    NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto,
    PerfilUsuario, CifrasInstitucionales,
)

def limpiar_texto(texto):
    if not texto:
        return ''
    texto = unicodedata.normalize('NFD', texto)
    texto = re.sub(r'[\u0300-\u036f]', '', texto)
    return re.sub(r'[^a-zA-Z0-9]', '', texto).lower()

def generar_username(nombres, apellidos):
    """
    Genera el nombre de usuario institucional automáticamente:
    Ejemplo: Aura Carolina Morán Sarate -> amorans (inicial 1er nombre + 1er apellido + inicial 2do apellido)
    """
    nombres_parts = [limpiar_texto(p) for p in nombres.strip().split() if p.strip()]
    apellidos_parts = [limpiar_texto(p) for p in apellidos.strip().split() if p.strip()]

    letra_nombre = nombres_parts[0][0] if nombres_parts else 'u'
    primer_apellido = apellidos_parts[0] if apellidos_parts else 'usuario'
    segunda_letra_apellido = apellidos_parts[1][0] if len(apellidos_parts) > 1 else ''

    base = f"{letra_nombre}{primer_apellido}{segunda_letra_apellido}"
    username = base
    contador = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{contador}"
        contador += 1
    return username


class NoticiaComunicadoForm(forms.ModelForm):
    class Meta:
        model = NoticiaComunicado
        fields = ['titulo', 'tipo', 'resumen', 'contenido', 'imagen', 'destacado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Convocatoria a Padres de Familia'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'resumen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Breve resumen descriptivo (1 o 2 líneas)'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Texto detallado del comunicado o noticia...'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FotoGaleriaForm(forms.ModelForm):
    class Meta:
        model = FotoGaleria
        fields = ['titulo', 'categoria', 'imagen', 'descripcion', 'activa']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Acto Cívico de Juramento'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Breve pie de foto o detalle de la actividad'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DocentePersonalForm(forms.ModelForm):
    funciones = forms.MultipleChoiceField(
        label='Funciones y cargos',
        choices=DocentePersonal.FUNCION_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        help_text='Puedes seleccionar varias opciones, por ejemplo Docente, Tutor/a y Rector/a.',
    )
    jornadas = forms.MultipleChoiceField(
        label='Jornadas o secciones',
        choices=DocentePersonal.JORNADA_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        help_text='Selecciona todos los turnos o secciones donde trabaja.',
    )
    asignaturas = forms.CharField(
        label='Materias o asignaturas',
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Ej. Lengua y Literatura, Matemática, Ciencias Naturales',
        }),
        help_text='Si imparte varias, sepáralas con comas.',
    )

    class Meta:
        model = DocentePersonal
        fields = ['nombres', 'apellidos', 'cargo', 'foto', 'orden', 'activo']
        labels = {'cargo': 'Detalle del cargo o curso (opcional)'}
        help_texts = {'cargo': 'Indica el curso de tutoría u otra responsabilidad si hace falta.'}
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Lcda. María'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Guamán'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Tutor de 4to EGB'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['funciones'].initial = self.instance.funciones_asignadas
            self.fields['jornadas'].initial = self.instance.jornadas_asignadas
            self.fields['asignaturas'].initial = ', '.join(self.instance.asignaturas_display)
        else:
            self.fields['funciones'].initial = ['docente']
            self.fields['jornadas'].initial = ['matutina']

    def clean_asignaturas(self):
        texto = self.cleaned_data.get('asignaturas', '')
        materias = []
        vistas = set()
        for materia in re.split(r'[,;\n]+', texto):
            materia = ' '.join(materia.split())
            clave = materia.casefold()
            if materia and clave not in vistas:
                materias.append(materia)
                vistas.add(clave)
        return materias

    def save(self, commit=True):
        docente = super().save(commit=False)
        docente.funciones = self.cleaned_data['funciones']
        docente.jornadas = self.cleaned_data['jornadas']
        docente.asignaturas = self.cleaned_data['asignaturas']
        docente.jornada = next(
            (jornada for jornada, _ in DocentePersonal.JORNADA_CHOICES if jornada in docente.jornadas),
            'matutina',
        )
        docente.area = ', '.join(docente.asignaturas)[:120]
        if commit:
            docente.save()
        return docente


class MensajeContactoForm(forms.ModelForm):
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@correo.com', 'autocomplete': 'email'}),
    )
    nivel_interes = forms.ChoiceField(
        label='Nivel educativo de interés',
        choices=[('', 'Seleccione un nivel...'), *MensajeContacto.NIVEL_INTERES_CHOICES],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    mensaje = forms.CharField(
        label='Mensaje',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos qué información necesitas...',
        }),
    )
    acepta_privacidad = forms.BooleanField(
        label='Acepto que la institución use mis datos para responder esta solicitud.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = MensajeContacto
        fields = ['nombre', 'telefono', 'email', 'nivel_interes', 'mensaje', 'acepta_privacidad']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. María García', 'autocomplete': 'name'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel', 'inputmode': 'tel', 'autocomplete': 'tel', 'placeholder': 'Ej. 096 017 2899'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle de su consulta sobre matrículas o certificados...'}),
        }


    def clean_nombre(self):
        return ' '.join(self.cleaned_data['nombre'].split())


class CifrasInstitucionalesForm(forms.ModelForm):
    class Meta:
        model = CifrasInstitucionales
        fields = ['total_estudiantes']
        widgets = {
            'total_estudiantes': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': 0,
                'step': 1,
                'placeholder': 'Ej. 350',
            }),
        }


class ConsultaSeguimientoForm(forms.ModelForm):
    prioridad = forms.TypedChoiceField(
        label='Prioridad',
        choices=MensajeContacto.PRIORIDAD_CHOICES,
        coerce=int,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    fecha_seguimiento = forms.DateTimeField(
        label='Recordarme el',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control form-control-sm', 'type': 'datetime-local'},
        ),
    )

    class Meta:
        model = MensajeContacto
        fields = ['prioridad', 'fecha_seguimiento']


class UsuarioCrearForm(forms.Form):
    nombres = forms.CharField(label='Nombres completos', max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Ej. Aura Carolina', 'id': 'id_nombres'
    }))
    apellidos = forms.CharField(label='Dos apellidos', max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Ej. Morán Sarate', 'id': 'id_apellidos'
    }))
    cedula = forms.CharField(label='Número de Cédula (Contraseña temporal)', max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Ej. 0923456789'
    }), help_text='La cédula se usará como su primera contraseña provisoria.')
    email = forms.EmailField(label='Correo Electrónico', required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'correo@ejemplo.com'
    }))
    rol = forms.ChoiceField(label='Rol y Permisos', choices=PerfilUsuario.ROLES_CHOICES, initial='docente', widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    foto = forms.ImageField(label='Fotografía de Perfil (Opcional)', required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control'
    }))

    def clean_nombres(self):
        return ' '.join(self.cleaned_data['nombres'].split())

    def clean_apellidos(self):
        apellidos = ' '.join(self.cleaned_data['apellidos'].split())
        if len(apellidos.split()) < 2:
            raise forms.ValidationError('Escribe los dos apellidos: paterno y materno.')
        return apellidos

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula', '').strip()
        if not cedula:
            raise forms.ValidationError('El número de cédula es obligatorio.')
        return cedula

    def save(self):
        nombres = self.cleaned_data['nombres'].strip()
        apellidos = self.cleaned_data['apellidos'].strip()
        cedula = self.cleaned_data['cedula'].strip()
        email = self.cleaned_data.get('email', '').strip()
        rol = self.cleaned_data['rol']
        foto = self.cleaned_data.get('foto')

        username = generar_username(nombres, apellidos)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=cedula,
            first_name=nombres.split()[0] if nombres else '',
            last_name=apellidos.split()[0] if apellidos else ''
        )

        if rol == 'administrador':
            user.is_staff = True
            user.save()

        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={
                'cedula': cedula,
                'nombres': nombres,
                'apellidos': apellidos,
                'rol': rol,
                'foto': foto,
                'debe_cambiar_password': True
            }
        )
        return user


class UsuarioEditarForm(forms.Form):
    nombres = forms.CharField(label='Nombres', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label='Apellidos', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cedula = forms.CharField(label='Número de Cédula', max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo Electrónico', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(label='Rol y Permisos', choices=PerfilUsuario.ROLES_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    foto = forms.ImageField(label='Fotografía de Perfil', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    activo = forms.BooleanField(label='Usuario Activo', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class PerfilPropioEditarForm(forms.Form):
    nombres = forms.CharField(label='Nombres', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label='Apellidos', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cedula = forms.CharField(label='Número de Cédula', max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo Electrónico', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    foto = forms.ImageField(label='Fotografía de Perfil', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))


class CambiarPasswordForm(forms.Form):
    nuevo_password = forms.CharField(
        label='Nueva Contraseña Personal',
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 6 caracteres',
            'id': 'id_nuevo_password'
        })
    )
    confirmar_password = forms.CharField(
        label='Confirmar Nueva Contraseña',
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita la contraseña exactamente',
            'id': 'id_confirmar_password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nuevo_password')
        p2 = cleaned_data.get('confirmar_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden. Por favor verifique.')
        return cleaned_data
