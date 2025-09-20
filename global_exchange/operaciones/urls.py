from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulador_operaciones, name="operaciones"),
    path("verificar/", views.verificar_tasa, name="verificar_tasa"),
    path("horaservidor/", views.hora_servidor, name="hora_servidor"),
]
