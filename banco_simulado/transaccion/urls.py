
from django.contrib import admin
from django.urls import path
from transaccion import views
urlpatterns = [
    path('cuenta/<str:nro_cuenta>/', views.obtener_cuenta, name='obtener_cuenta'),
    path('cuentas/documento/<str:documento>/', views.obtener_cuentas_por_documento, name='cuentas_por_documento'),
]
