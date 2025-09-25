"""
ASGI configuration for the ``global_exchange`` project.

Este archivo expone el callable ASGI a nivel de módulo como ``application``.  
ASGI es el estándar de Python para la comunicación asíncrona entre servidores web 
y aplicaciones Django (soporta WebSockets y HTTP).

Uso:
    - Este archivo es usado por servidores ASGI como Daphne o Uvicorn.
    - No necesita modificación para entornos de producción típicos.
    - Asegura que Django cargue la configuración correcta del proyecto.

Referencias:
    - Documentación de despliegue Django ASGI: 
      https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')

application = get_asgi_application()
