import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import notificaciones.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notificaciones.routing.websocket_urlpatterns
        )
    ),
})
