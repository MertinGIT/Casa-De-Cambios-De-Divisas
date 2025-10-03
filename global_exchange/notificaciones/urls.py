# notificaciones/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.panel_alertas, name="notificaciones"),
    path("guardar-configuracion/", views.guardar_configuracion, name="guardar_configuracion"),
]