"""
Configuración principal de URLs del proyecto EEB ANTONIO ANTE.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# En entorno de desarrollo, Django sirve directamente los archivos multimedia subidos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
