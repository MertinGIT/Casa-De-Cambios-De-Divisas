from django.urls import path
from .views import cliente_usuarios_lista, editar_cliente_usuario, cliente_usuario_detalle

urlpatterns = [
    path('cliente_usuario/', cliente_usuarios_lista, name='cliente_usuario'),
    path('cliente_usuario/editar/<int:id>/', editar_cliente_usuario, name='editar_cliente_usuario'),
    path('cliente_usuario/detalle/<int:pk>/', cliente_usuario_detalle, name='cliente_usuario_detalle'),
]
