
"""
Django settings for EEB ANTONIO ANTE project.
Django 5.2 | Neon PostgreSQL | Vercel | WhiteNoise
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


# ==========================================================
# 1. DIRECTORIOS DEL PROYECTO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Variables locales desde .env
load_dotenv(BASE_DIR / ".env")


# ==========================================================
# 2. FUNCIONES PARA VARIABLES DE ENTORNO
# ==========================================================

def env_bool(name, default=False):
    """Convierte variables de entorno en valores booleanos."""

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in (
        "true", "1", "t", "yes", "on"
    )


# Detectar Vercel
IS_VERCEL = env_bool("VERCEL", default=False)


# ==========================================================
# 3. SEGURIDAD Y CLAVE SECRETA
# ==========================================================

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY no está configurada en las variables de entorno."
    )


DEBUG = env_bool(
    "DEBUG",
    default=not IS_VERCEL
)


# ==========================================================
# 4. HOSTS PERMITIDOS
# ==========================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".vercel.app",
]

# Dominios proporcionados automáticamente por Vercel
for variable in (
    "VERCEL_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
):
    host = os.getenv(variable, "").strip()

    if host:
        host = (
            host.removeprefix("https://")
                .removeprefix("http://")
                .rstrip("/")
        )

        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)


# Dominios adicionales opcionales
extra_hosts = os.getenv("ALLOWED_HOSTS", "")

if extra_hosts:
    ALLOWED_HOSTS.extend(
        host.strip()
        for host in extra_hosts.split(",")
        if host.strip()
    )


# ==========================================================
# 5. PROTECCIÓN CSRF
# ==========================================================

CSRF_TRUSTED_ORIGINS = [
    "https://antonio-ante-qq7h.vercel.app",
]

# Incluir dominio de producción y Preview
for variable in (
    "VERCEL_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
):
    host = os.getenv(variable, "").strip()

    if host:
        host = (
            host.removeprefix("https://")
                .removeprefix("http://")
                .rstrip("/")
        )

        origin = f"https://{host}"

        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)


# Dominios CSRF adicionales opcionales
extra_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")

if extra_csrf:
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip()
        for origin in extra_csrf.split(",")
        if origin.strip()
    )


# ==========================================================
# 6. CONFIGURACIÓN HTTPS
# ==========================================================

SECURE_SSL_REDIRECT = env_bool(
    "SECURE_SSL_REDIRECT",
    default=not DEBUG
)

SESSION_COOKIE_SECURE = env_bool(
    "SESSION_COOKIE_SECURE",
    default=not DEBUG
)

CSRF_COOKIE_SECURE = env_bool(
    "CSRF_COOKIE_SECURE",
    default=not DEBUG
)

# Vercel utiliza un proxy HTTPS
if IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

# HSTS: activar solamente después de verificar HTTPS
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "0")
)

if SECURE_HSTS_SECONDS < 0:
    raise ImproperlyConfigured(
        "SECURE_HSTS_SECONDS debe ser cero o positivo."
    )

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False
)

SECURE_HSTS_PRELOAD = env_bool(
    "SECURE_HSTS_PRELOAD",
    default=False
)


# ==========================================================
# 7. APLICACIONES INSTALADAS
# ==========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Aplicación principal
    "core.apps.CoreConfig",
]


# ==========================================================
# 8. MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise debe estar inmediatamente después
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# 9. URLS Y WSGI
# ==========================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ==========================================================
# 10. CONFIGURACIÓN DE PLANTILLAS
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "core" / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]


# ==========================================================
# 11. BASE DE DATOS
# SQLITE LOCAL / NEON POSTGRESQL EN VERCEL
# ==========================================================

if IS_VERCEL:

    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    if not DATABASE_URL:
        raise ImproperlyConfigured(
            "DATABASE_URL no está configurada en Vercel."
        )

    try:
        import dj_database_url

        DATABASES = {
            "default": dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=0,
                ssl_require=True,
            )
        }

        # Compatible con el pooler de Neon
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

    except Exception as exc:
        raise ImproperlyConfigured(
            f"Error configurando PostgreSQL: {exc}"
        ) from exc

else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ==========================================================
# 12. VALIDADORES DE CONTRASEÑAS
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==========================================================
# 13. INTERNACIONALIZACIÓN
# ==========================================================

LANGUAGE_CODE = "es"

TIME_ZONE = "America/Guayaquil"

USE_I18N = True

USE_TZ = True


# ==========================================================
# 14. ARCHIVOS ESTÁTICOS
# CSS / JAVASCRIPT / IMÁGENES DEL DISEÑO
# ==========================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_DIR = BASE_DIR / "core" / "static"

STATICFILES_DIRS = (
    [STATIC_DIR]
    if STATIC_DIR.is_dir()
    else []
)


# WhiteNoise para producción
STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


# ==========================================================
# 15. ARCHIVOS MULTIMEDIA
# FOTOGRAFÍAS / DOCUMENTOS / GALERÍAS
# ==========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ==========================================================
# 16. CLAVES PRIMARIAS
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# 17. AUTENTICACIÓN Y REDIRECCIONES
# ==========================================================

LOGIN_URL = "core:login"

LOGIN_REDIRECT_URL = "/admin/"

LOGOUT_REDIRECT_URL = "core:home"
