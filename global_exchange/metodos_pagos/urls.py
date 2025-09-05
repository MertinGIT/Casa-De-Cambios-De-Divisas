from django.urls import path, include
from .views import (
    MetodoPagoListView, 
    MetodoPagoCreateView, 
    MetodoPagoUpdateView,
    MetodoPagoDesactivateView, 
    MetodoPagoActivateView,
    validar_nombre_metodo_pago
)
from metodos_pagos import views as mp_views

urlpatterns = [
    path('', MetodoPagoListView.as_view(), name='metodos_pagos'),
    path('agregar/', mp_views.MetodoPagoCreateView.as_view(), name='metodos-pagos-agregar'),
    path('editar/<int:pk>/', mp_views.MetodoPagoUpdateView.as_view(), name='metodos-pagos-editar'),
    path('detalle/<int:pk>/', mp_views.MetodoPago_detalle, name='metodos-pagos-detalle'),
    path('desactivate/<int:pk>/', mp_views.MetodoPagoDesactivateView.as_view(), name='metodos-pagos-desactivate'),
    path('activate/<int:pk>/', mp_views.MetodoPagoActivateView.as_view(), name='metodos-pagos-activate'),
    path('validar-nombre/', mp_views.validar_nombre_metodo_pago, name='metodos-pagos-validar-nombre'),
]