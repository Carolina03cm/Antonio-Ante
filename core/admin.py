from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto,
    PerfilUsuario, CifrasInstitucionales, OfertaAcademica,
)

# Personalización del Panel Administrativo Oficial de Django
admin.site.site_header = "EEB Antonio Ante • Administración"
admin.site.site_title = "EEB Antonio Ante"
admin.site.index_title = "Panel de Administración Institucional"

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombres', 'apellidos', 'cedula', 'rol', 'debe_cambiar_password')
    list_filter = ('rol', 'debe_cambiar_password')
    search_fields = ('user__username', 'nombres', 'apellidos', 'cedula')

@admin.register(CifrasInstitucionales)
class CifrasInstitucionalesAdmin(admin.ModelAdmin):
    list_display = ('total_estudiantes',)
    fields = ('total_estudiantes',)

    def has_add_permission(self, request):
        return not CifrasInstitucionales.objects.filter(pk=1).exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(NoticiaComunicado)
class NoticiaComunicadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'destacado', 'fecha_publicacion', 'autor')
    list_filter = ('tipo', 'destacado', 'fecha_publicacion')
    search_fields = ('titulo', 'resumen', 'contenido')
    date_hierarchy = 'fecha_publicacion'
    list_editable = ('destacado',)
    ordering = ('-fecha_publicacion',)

@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'activa', 'fecha_subida', 'miniatura')
    list_filter = ('categoria', 'activa', 'fecha_subida')
    search_fields = ('titulo', 'descripcion')
    list_editable = ('activa',)

    def miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.imagen.url)
        return '—'
    miniatura.short_description = 'Vista previa'

@admin.register(DocentePersonal)
class DocentePersonalAdmin(admin.ModelAdmin):
    list_display = ('foto_miniatura', 'apellidos', 'nombres', 'cargo', 'jornada', 'area', 'orden', 'activo')
    list_filter = ('jornada', 'activo')
    search_fields = ('nombres', 'apellidos', 'cargo', 'area')
    list_editable = ('orden', 'activo')
    ordering = ('jornada', 'orden', 'apellidos')

    def foto_miniatura(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />', obj.foto.url)
        initials = (obj.nombres[0] if obj.nombres else '') + (obj.apellidos[0] if obj.apellidos else '')
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:#18396D;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:0.8rem;">{}</div>',
            initials.upper()
        )
    foto_miniatura.short_description = 'Foto'

@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'fecha_envio', 'estado_badge')
    list_filter = ('leido', 'fecha_envio')
    search_fields = ('nombre', 'telefono', 'mensaje')
    readonly_fields = ('nombre', 'telefono', 'mensaje', 'fecha_envio')
    ordering = ('-fecha_envio',)

    def estado_badge(self, obj):
        if obj.leido:
            return format_html('<span style="color:green;font-weight:bold;">✔ Atendido</span>')
        return format_html('<span style="color:#D71926;font-weight:bold;">⏳ Pendiente</span>')
    estado_badge.short_description = 'Estado'

    def has_add_permission(self, request):
        return False

@admin.register(OfertaAcademica)
class OfertaAcademicaAdmin(admin.ModelAdmin):
    list_display = ('nivel', 'actualizada')
    list_editable = ()
    fields = ('nivel', 'imagen', 'actualizada')
    readonly_fields = ('actualizada',)