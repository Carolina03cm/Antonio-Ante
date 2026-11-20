import unicodedata
import re
from django import forms
from django.contrib.auth.models import User
from .models import NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto, PerfilUsuario

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
    class Meta:
        model = DocentePersonal
        fields = ['nombres', 'apellidos', 'cargo', 'jornada', 'area', 'foto', 'orden', 'activo']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Lcda. María'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Guamán'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Docente Tutora 3° EGB'}),
            'jornada': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Educación Básica, Matemáticas'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MensajeContactoForm(forms.ModelForm):
    class Meta:
        model = MensajeContacto
        fields = ['nombre', 'telefono', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Su nombre y apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 096 017 2899'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle de su consulta sobre matrículas o certificados...'}),
        }


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
