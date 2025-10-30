from django.urls import path
from . import views

urlpatterns = [
    # Paso 1: Selección de localidad (TAUSER)
    path('', views.atm_seleccionar_localidad, name='atm_seleccionar_localidad'),
    
    # Paso 2: Login con cédula y contraseña
    path('login/', views.atm_login, name='atm_login'),
    
    # Paso 3: Selección de cliente (NUEVA RUTA)
    path('seleccionar-cliente/', views.atm_seleccionar_cliente, name='atm_seleccionar_cliente'),
    
    # Paso 4: Dashboard y operaciones
    path('dashboard/', views.atm_dashboard, name='atm_dashboard'),
    path('depositar/', views.atm_depositar, name='atm_depositar'),
    path('extraer/', views.atm_extraer, name='atm_extraer'),
    path('transacciones/', views.atm_transacciones, name='atm_transacciones'),
    
    # Logout
    path('logout/', views.atm_logout, name='atm_logout'),
]