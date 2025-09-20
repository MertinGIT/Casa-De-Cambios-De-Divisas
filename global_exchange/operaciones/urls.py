from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulador_operaciones, name="operaciones"),
    path("obtener-metodos/", views.obtener_metodos_pago, name="obtener_metodos_pago"),
    path("guardar-metodo/", views.guardar_metodo_pago, name="guardar_metodo_pago"),
]
