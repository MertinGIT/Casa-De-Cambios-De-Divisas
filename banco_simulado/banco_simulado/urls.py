
from django.contrib import admin
from django.urls import path
from transaccion import views
from transaccion.views import cliente_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('clientes/', cliente_view, name="cliente_view"),
    path('transaccion/', views.transaccion_banco_view),
]
