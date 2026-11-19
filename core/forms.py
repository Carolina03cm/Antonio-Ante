from django import forms
from .models import NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto

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
        fields = ['nombres', 'apellidos', 'cargo', 'jornada', 'area', 'orden', 'activo']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Lcda. María'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Guamán'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Docente Tutora 3° EGB'}),
            'jornada': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Educación Básica, Matemáticas'}),
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
