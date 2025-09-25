"""
WSGI configuration for the ``global_exchange`` project.

Este archivo expone el callable WSGI a nivel de módulo como ``application``.  
WSGI es el estándar de Python para la comunicación entre servidores web y aplicaciones Django.

Uso:
    - Este archivo es usado por servidores WSGI como Gunicorn o uWSGI.
    - No necesita modificación para entornos de producción típicos.
    - Asegura que Django cargue la configuración correcta del proyecto.

Referencias:
    - Documentación de despliegue Django: 
      https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')

application = get_wsgi_application()
