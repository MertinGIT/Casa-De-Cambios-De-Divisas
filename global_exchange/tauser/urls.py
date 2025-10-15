from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.atm_login, name='atm_login'),
    path('logout/', views.atm_logout, name='atm_logout'),
    path('dashboard/', views.atm_dashboard, name='atm_dashboard'),
    path('transacciones/', views.atm_transacciones, name='atm_transacciones'),
    path('depositar/', views.atm_depositar, name='atm_depositar'),
    path('extraer/', views.atm_extraer, name='atm_extraer'),
    path('logout/', views.atm_logout, name='atm_logout'),
]