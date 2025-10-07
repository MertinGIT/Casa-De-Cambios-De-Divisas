# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.configuracion_view_usuario, name='configuracion_usuario'),
    path("mfa_configuration/", views.mfa_configuration, name="mfa_configuration")
]
