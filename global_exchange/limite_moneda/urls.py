from django.urls import path
from . import views

urlpatterns = [
    # Lista de límites
    path('', views.lista_limites, name='lista-limites'),

    # Validación de nombre de cliente
    path('check-nombre-cliente/', views.check_nombre_cliente, name='check-nombre-cliente'),

    # Crear límite
    path('crear/', views.crear_limite, name='limite-crear'),

    # Editar límite
    path('editar/<int:pk>/', views.editar_limite, name='limite-editar'),

    # Cambiar estado
    path('cambiar-estado/<int:pk>/', views.cambiar_estado_limite, name='limite-cambiar-estado'),

    # Detalle para modal
    path('detalle/<int:pk>/', views.limite_detalle, name='limite-detalle'),
    path('ajax/clientes/', views.get_clientes, name='get_clientes'),
    path('ajax/monedas/', views.get_monedas, name='get_monedas'),
]