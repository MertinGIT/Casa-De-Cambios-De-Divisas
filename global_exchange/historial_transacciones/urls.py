from django.urls import path
from . import views

app_name = 'historial_transacciones'

urlpatterns = [
    path('', views.historial_usuario, name='historial_usuario'),
    path('detalle/<int:transaccion_id>/', views.detalle_transaccion, name='detalle_transaccion'),
    path('export/excel/', views.exportar_historial_excel, name='exportar_historial_excel'),
    path('export/pdf/', views.exportar_historial_pdf, name='exportar_historial_pdf'),
]