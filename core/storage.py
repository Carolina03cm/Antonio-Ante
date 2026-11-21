"""
Almacenamiento de archivos para Django usando Vercel Blob.

En producción (Vercel) se usa el store público conectado al proyecto.
En desarrollo local, settings.py conserva FileSystemStorage.
"""
from io import BytesIO
import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from vercel.blob import sync as blob


@deconstructible
class VercelBlobStorage(Storage):
    """Backend Django para guardar y servir archivos desde Vercel Blob."""

    def _save(self, name, content):
        # Las funciones de Vercel reciben el archivo enviado al servidor.
        # Para fotos institucionales pequeñas, leemos el contenido en memoria.
        if hasattr(content, "seek"):
            content.seek(0)

        data = content.read()
        if not isinstance(data, bytes):
            data = data.encode("utf-8")

        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )

        uploaded = blob.put_blob(
            name,
            data,
            access="public",
            content_type=content_type,
            add_random_suffix=True,
        )

        # Se guarda la URL pública completa en el ImageField.
        # Los ImageField del proyecto se amplían a max_length=500.
        return uploaded.url

    def _open(self, name, mode="rb"):
        result = blob.get_blob(name, access="public")
        return ContentFile(result.body, name=name)

    def delete(self, name):
        if name:
            blob.delete_blob(name)

    def exists(self, name):
        if not name:
            return False
        try:
            blob.head_blob(name)
            return True
        except blob.BlobNotFoundError:
            return False

    def size(self, name):
        return blob.head_blob(name).size

    def url(self, name):
        # Los archivos nuevos ya tienen una URL absoluta de Vercel Blob.
        if name.startswith(("https://", "http://")):
            return name

        # Compatibilidad con registros antiguos que todavía guardan rutas.
        # Esas rutas solo funcionarán si el archivo existe en MEDIA_ROOT.
        from django.conf import settings
        return f"{settings.MEDIA_URL.rstrip('/')}/{name.lstrip('/')}"

    def path(self, name):
        raise NotImplementedError(
            "Vercel Blob no proporciona rutas locales del sistema de archivos."
        )
