from django.urls import path
from . import views

urlpatterns = [
    path("", views.cotizacion_lista, name="cotizacion"),
    path("nuevo/", views.cotizacion_nuevo, name="cotizacion_nuevo"),
    path("editar/<int:pk>/", views.cotizacion_editar, name="cotizacion_editar"),
    path("eliminar/<int:pk>/", views.cotizacion_desactivar, name="cotizacion_desactivar"),
    path('cotizaciones/detalle/<int:pk>/', views.cotizacion_detalle, name='cotizacion_detalle'),
]
