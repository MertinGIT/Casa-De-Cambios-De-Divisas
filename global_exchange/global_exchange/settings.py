"""

Configuración principal de Django para el proyecto ``global_exchange``.

Este archivo contiene la configuración global del proyecto.  
Está dividido en secciones clave que cubren seguridad, aplicaciones instaladas, 
middleware, base de datos, plantillas, internacionalización, archivos estáticos 
y autenticación de usuarios.

Referencias:
    - Documentación oficial de Django: 
      https://docs.djangoproject.com/en/4.1/topics/settings/
    - Lista completa de configuraciones disponibles: 
      https://docs.djangoproject.com/en/4.1/ref/settings/

Secciones documentadas:
    - Seguridad
    - Email
    - Aplicaciones instaladas
    - Middleware
    - Configuración de plantillas
    - Base de datos
    - Validación de contraseñas
    - Internacionalización
    - Archivos estáticos
    - Autenticación

"""

from logging import config
from pathlib import Path
import environ
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde .env

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
env = environ.Env(
    DEBUG=(bool, False)   
)
BASE_DIR = Path(__file__).resolve().parent.parent

# Leer archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# ============================================================================
# Seguridad
# ============================================================================
#: Clave secreta de Django. **Nunca debe compartirse ni versionarse.**
SECRET_KEY = env('DJANGO_SECRET_KEY')



#: Lista de hosts permitidos para el despliegue.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# ============================================================================
# Configuracion de Email
# ============================================================================
#: Configuración del backend de correos electrónicos.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'rodriguezmartinv02@gmail.com'
EMAIL_HOST_PASSWORD = 'wljrsfybvpahpcha'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

#: Tiempo de expiración de links de reseteo de contraseña (en segundos).
PASSWORD_RESET_TIMEOUT = 14400  # 4 horas


# ============================================================================
# Aplicaciones instaladas
# ============================================================================

INSTALLED_APPS = [
    'daphne',
    #'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'usuarios',
    'widget_tweaks',
    'clientes',
    'roles_permisos',
    'admin_dashboard',
    'configuracion',
    'cliente_segmentacion',
    'cotizaciones',
    'monedas',
    'metodos_pagos',
    'cliente_usuario',
    'operaciones',  
    'medio_acreditacion',
    'corsheaders',
    'limite_moneda',
    'historial_transacciones',
    'channels',
    'notificaciones',
    'configuracion_usuario',
    'admin_transacciones',
    'tauser',
    'facturacion'
]


# Configuración Factura Segura
FACTURA_SEGURA = {
    'AMBIENTE': 'test',  
    'API_URL': 'https://apitest.facturasegura.com.py/misife00/v1/esi',
    'TOKEN': 'eyJ2ZXIiOiI1IiwidWlkIjoiMWVlOTRiNmI3MDgyNDBhMDhiY2E5YTgwZWExODJhOTgiLCJzaWQiOjAsImV4cCI6MH0.aPfwVQ.tcnm1XzTnrCnhXyVaOKP9ljPxfo',
    'RUC_EMISOR': '2595733',
    'DV_EMISOR': '3',
    'TIMBRADO': '80143335',
    'FECHA_INICIO_TIMBRADO': '2023-12-27',
    'ESTABLECIMIENTO': '001',
    'PUNTO_EXPEDICION': '003',
}

# Configuración ASGI (reemplaza WSGI para WebSockets)
ASGI_APPLICATION = 'global_exchange.asgi.application'
# Configuración de Channels con Redis

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}
# ============================================================================
# Middleware
# ============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # <- Debe ir primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'global_exchange.middleware.Custom404Middleware',
    'roles_permisos.middleware.RoleBasedMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8001",  # donde corre tu frontend tauser
    "http://127.0.0.1:8002", 
]
CORS_ALLOW_CREDENTIALS = True
# ============================================================================
# Configuración de plantillas
# ============================================================================
ROOT_URLCONF = 'global_exchange.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'global_exchange.wsgi.application'


# ============================================================================
# Base de datos
# ============================================================================

JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", SECRET_KEY)

SIMPLE_JWT = {
    "ALGORITHM": "HS256",
    "SIGNING_KEY": 'clave_super_secreta_compartida_local',   # usado para firmar/verificar HS256
    # opcionales:
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

SECRET_KEY = env('DJANGO_SECRET_KEY')
#: Modo debug (activar solo en desarrollo).
DEBUG = os.getenv("DEBUG", "true").lower() == "true" 

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DJANGO_DB_NAME'),
        'USER': env('DJANGO_DB_USER'),
        'PASSWORD': env('DJANGO_DB_PASSWORD'),
        'HOST': env('DJANGO_DB_HOST'),  # debe ser 'db' para conectar al contenedor postgres
        'PORT': env('DJANGO_DB_PORT'),
    }
}

# Permitir solo tu frontend  
#CORS_ALLOWED_ORIGINS = [
#    "http://localhost:8000",
#]
CORS_ALLOW_ALL_ORIGINS = True
# ⚠️ Si querés permitir todos (solo en desarrollo):
# CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]
# ============================================================================
# Validación de contraseñas
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # 👈 mínimo de 8 caracteres
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================================
# Internacionalización
# ============================================================================

LANGUAGE_CODE = 'es'

#TIME_ZONE = 'UTC'
TIME_ZONE = 'America/Asuncion'
USE_I18N = True
USE_L10N = True  # 👈 importante también
#USE_TZ = True


# ============================================================================
# Archivos estáticos
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ============================================================================
# Autenticación
# ============================================================================

#: Ruta de redirección al login cuando un usuario no está autenticado.
LOGIN_URL='/login/' 

#: Tipo de clave primaria por defecto.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#: Modelo de usuario personalizado usado en el proyecto.
AUTH_USER_MODEL = 'usuarios.CustomUser'