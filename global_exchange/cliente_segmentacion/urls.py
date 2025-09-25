from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_segmentaciones, name='lista-segmentaciones'),
    path('agregar/', views.crear_segmentacion, name='segmentaciones-agregar'),
    path('editar/<int:pk>/', views.editar_segmentacion, name='segmentaciones-editar'),
    path('changeState/<int:pk>/', views.cambiar_estado_segmentacion, name='segmentaciones-state'),
    path('detalle/<int:pk>/', views.segmentacion_detalle, name='segmentacion-detalle'),
    path("check-nombre/", views.check_nombre_segmentacion, name="check-nombre-segmentacion"),

]
