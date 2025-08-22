from django.urls import path
from . import views

urlpatterns = [
    path("", views.rol_lista, name="roles"),
    path("nuevo/", views.rol_nuevo, name="rol_nuevo"),
    path("editar/<int:pk>/", views.rol_editar, name="rol_editar"),
    path("eliminar/<int:pk>/", views.rol_eliminar, name="rol_eliminar"),
    path('roles/detalle/<int:pk>/', views.rol_detalle, name='rol_detalle'),
]
