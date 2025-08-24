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
SECRET_KEY = 'django-insecure-a59ch^c$8!qa+s&5@-zq-=q_cyz!e5!x@hsqg8dsa7_sr-t^s&'



#: Lista de hosts permitidos para el despliegue.
ALLOWED_HOSTS = ['192.168.0.11', '127.0.0.1', 'localhost']

# ============================================================================
# Configuracion de Email
# ============================================================================
#: Configuración del backend de correos electrónicos.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = env('EMAIL_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
EMAIL_PORT = 587
EMAIL_USE_TLS = True

#: Tiempo de expiración de links de reseteo de contraseña (en segundos).
PASSWORD_RESET_TIMEOUT = 14400  # 4 horas


# ============================================================================
# Aplicaciones instaladas
# ============================================================================

INSTALLED_APPS = [
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
    'asignar_clientes_usuarios',
]
# ============================================================================
# Middleware
# ============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'global_exchange.middleware.Custom404Middleware',
]

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



# ============================================================================
# Validación de contraseñas
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ============================================================================
# Archivos estáticos
# ============================================================================

STATIC_URL = '/static/'
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