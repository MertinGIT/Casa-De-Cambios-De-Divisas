from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_transacciones, name='listar_transacciones'),
    path('cambiar-estado/', views.cambiar_estado_transaccion, name='cambiar_estado_transaccion'),
    path('estadisticas/', views.estadisticas_transacciones, name='estadisticas_transacciones'),
]