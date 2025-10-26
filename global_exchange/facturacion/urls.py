from django.urls import path
from . import views


app_name = 'facturas'

urlpatterns = [
    path('estado/<int:factura_id>/', views.consultar_estado_factura, name='consultar_estado'),
    path('generar-factura/', views.generar_factura_transaccion, name='generar_factura_transaccion'),
    path('consultar-factura/', views.consultar_estado_factura_transaccion, name='consultar_factura_transaccion'),
    path('descargar-factura/', views.descargar_factura, name='descargar_factura'),
    path('enviar-email/', views.enviar_factura_email, name='enviar_factura_email'),]