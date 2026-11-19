from django.contrib import admin
from .models import NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto

# Personalización del Panel Administrativo Oficial de Django
admin.site.site_header = "EEB ANTONIO ANTE • Panel de Gestión Escolar"
admin.site.site_title = "EEB Antonio Ante"
admin.site.index_title = "Módulo de Administración Institucional"

@admin.register(NoticiaComunicado)
class NoticiaComunicadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'destacado', 'fecha_publicacion', 'autor')
    list_filter = ('tipo', 'destacado', 'fecha_publicacion')
    search_fields = ('titulo', 'resumen', 'contenido')
    date_hierarchy = 'fecha_publicacion'
    list_editable = ('destacado',)

@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'activa', 'fecha_subida')
    list_filter = ('categoria', 'activa', 'fecha_subida')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('activa',)

@admin.register(DocentePersonal)
class DocentePersonalAdmin(admin.ModelAdmin):
    list_display = ('apellidos', 'nombres', 'cargo', 'jornada', 'area', 'orden', 'activo')
    list_filter = ('jornada', 'activo')
    search_fields = ('nombres', 'apellidos', 'cargo', 'area')
    list_editable = ('orden', 'activo')

@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'fecha_envio', 'leido')
    list_filter = ('leido', 'fecha_envio')
    search_fields = ('nombre', 'telefono', 'mensaje')
    list_editable = ('leido',)
    readonly_fields = ('nombre', 'telefono', 'mensaje', 'fecha_envio')
