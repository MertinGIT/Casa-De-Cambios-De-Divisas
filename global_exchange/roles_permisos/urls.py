from django.urls import path
from . import views
from .views import rol_lista, rol_nuevo, rol_editar, rol_eliminar, rol_detalle, rol_activar, rol_desactivar

urlpatterns = [
    path("", views.rol_lista, name="roles"),
    path("nuevo/", views.rol_nuevo, name="rol_nuevo"),
    path("editar/<int:pk>/", views.rol_editar, name="rol_editar"),
    path("eliminar/<int:pk>/", views.rol_eliminar, name="rol_eliminar"),
    path('roles/detalle/<int:pk>/', views.rol_detalle, name='rol_detalle'),
    path('activar/<int:pk>/', rol_activar, name='rol_activar'),
    path('desactivar/<int:pk>/', rol_desactivar, name='rol_desactivar'),
]
