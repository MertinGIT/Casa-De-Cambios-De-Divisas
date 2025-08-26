from django.urls import path, include
from .views import ClienteListView, ClienteCreateView, ClienteUpdateView, ClienteDeleteView,ClienteDesactivateView, ClienteActivateView
from clientes import views as clientes_views
urlpatterns = [
    path('', ClienteListView.as_view(), name='clientes'),
    path('agregar/', clientes_views.ClienteCreateView.as_view(), name='clientes-agregar'),
    path('editar/<int:pk>/', clientes_views.ClienteUpdateView.as_view(), name='clientes-editar'),
    path('eliminar/<int:pk>/', clientes_views.ClienteDeleteView.as_view(), name='clientes-eliminar'),
    path('detalle/<int:pk>/', clientes_views.cliente_detalle, name='clientes-detalle'),
    path('desactivate/<int:pk>/', clientes_views.ClienteDesactivateView.as_view(), name='clientes-desactivate'),
    path('activate/<int:pk>/', clientes_views.ClienteActivateView.as_view(), name='clientes-activate'),
    path("check-email/", clientes_views.check_email, name="clientes-check-email"),
]
