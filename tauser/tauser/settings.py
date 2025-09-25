import os
from pathlib import Path
import environ

# ==========================
# Inicializar django-environ
# ==========================
env = environ.Env(
    DJANGO_DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Leer archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ==========================
# CONFIGURACIÓN PRINCIPAL
# ==========================
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = ["*"]  # luego ponés el dominio/IP de tu server

# ==========================
# APPS INSTALADAS
# ==========================
INSTALLED_APPS = [
    # Tus apps locales
    'tauser_vista_principal',  
    'tauser_menu',
    # Apps esenciales de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # << necesaria para Permission, User, etc.
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
from datetime import datetime, timedelta

JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", SECRET_KEY)

SIMPLE_JWT = {
    "ALGORITHM": "HS256",
    "SIGNING_KEY": 'clave_super_secreta_compartida_local',   # usado para firmar/verificar HS256
    # opcionales:
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}


# ==========================
# MIDDLEWARE
# ==========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',          # << necesario
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',       # << necesario
    'django.contrib.messages.middleware.MessageMiddleware',          # << necesario
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_PASSWORD_VALIDATORS = []
ROOT_URLCONF = "tauser.urls"

# ==========================
# TEMPLATES
# ==========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Carpeta para templates globales
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tauser.wsgi.application"
ASGI_APPLICATION = "tauser.asgi.application"

# ==========================
# BASE DE DATOS
# ==========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DJANGO_DB_NAME"),
        "USER": env("DJANGO_DB_USER"),
        "PASSWORD": env("DJANGO_DB_PASSWORD"),
        "HOST": env("DJANGO_DB_HOST"),
        "PORT": env("DJANGO_DB_PORT"),
    }
}

# ==========================
# VALIDACIÓN DE USUARIOS
# ==========================


# ==========================
# INTERNACIONALIZACIÓN
# ==========================
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Asuncion"
USE_I18N = True
USE_TZ = True

# ==========================
# ARCHIVOS ESTÁTICOS
# ==========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==========================
# EMAIL
# ==========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")

# ==========================
# DEFAULT
# ==========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================
# Nota importante
# ==========================
# Tauser NO tiene que usar AUTH_USER_MODEL del proyecto del banco.
# Todas las tablas de auth y sessions se crean automáticamente al hacer migrate en este proyecto.
