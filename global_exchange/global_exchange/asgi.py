import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')

# ⚠️ Primero inicializar Django
django_asgi_app = get_asgi_application()

# 👇 Luego importar Channels (para que Django ya esté listo)
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import notificaciones.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notificaciones.routing.websocket_urlpatterns
        )
    ),
})
