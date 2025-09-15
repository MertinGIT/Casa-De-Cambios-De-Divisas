from django.urls import path
from . import views

urlpatterns = [
    path("", views.moneda_lista, name="monedas"),
    path("nuevo/", views.moneda_nueva, name="moneda_nueva"),
    path("editar/<int:pk>/", views.moneda_editar, name="moneda_editar"),
    path("eliminar/<int:pk>/", views.moneda_desactivar, name="moneda_desactivar"),
    path("detalle/<int:pk>/", views.moneda_detalle, name="moneda_detalle"),
]
