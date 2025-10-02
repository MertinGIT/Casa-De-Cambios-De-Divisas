# notificaciones/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.panel_alertas, name="panel_alertas"),
    path("guardar-configuracion/", views.guardar_configuracion, name="guardar_configuracion"),
    path("test/", views.test_notificaciones, name="test_notificaciones"),
]