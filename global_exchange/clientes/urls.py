from django.urls import path, include
from .views import ClienteListView, ClienteCreateView, ClienteUpdateView, ClienteDeleteView  
from clientes import views as clientes_views
urlpatterns = [
    path('', ClienteListView.as_view(), name='clientes'),
    path('agregar/', clientes_views.ClienteCreateView.as_view(), name='clientes-agregar'),
    path('editar/<int:pk>/', clientes_views.ClienteUpdateView.as_view(), name='clientes-editar'),
    path('eliminar/<int:pk>/', clientes_views.ClienteDeleteView.as_view(), name='clientes-eliminar'),
    path('detalle/<int:pk>/', clientes_views.cliente_detalle, name='clientes-detalle'),
]
