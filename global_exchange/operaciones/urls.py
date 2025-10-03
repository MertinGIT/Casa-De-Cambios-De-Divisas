from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulador_operaciones, name="operaciones"),
    path("verificar/", views.verificar_tasa, name="verificar_tasa"),
    path("horaservidor/", views.hora_servidor, name="hora_servidor"),
    path("obtener-metodos/", views.obtener_metodos_pago, name="obtener_metodos_pago"),
    path("guardar-metodo/", views.guardar_metodo_pago, name="guardar_metodo_pago"),
    path("guardar-transaccion/", views.guardar_transaccion, name="guardar_transaccion"),
    path('actualizar-estado-transaccion/', views.actualizar_estado_transaccion, name='actualizar_estado_transaccion'),
    path("enviar-pin/", views.enviar_pin, name="enviar_pin"),
    path("validar-pin/", views.validar_pin, name="validar_pin"),
    path('verificar-limites/', views.verificar_limites, name='verificar_limites'),
]