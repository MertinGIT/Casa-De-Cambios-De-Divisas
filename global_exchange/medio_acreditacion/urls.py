from django.urls import path
from . import views

urlpatterns = [
    path('entidades/', views.tipo_entidad_list, name='tipo_entidad_list'),
    path('entidades/crear/', views.tipo_entidad_create, name='tipo_entidad_create'),
    path('entidades/editar/<int:pk>/', views.tipo_entidad_update, name='tipo_entidad_update'),
    path('entidades/toggle/<int:pk>/', views.tipo_entidad_toggle, name='tipo_entidad_toggle'),
    path('entidades/detalle/<int:pk>/', views.tipo_entidad_detail, name='tipo_entidad_detail'),

    path('medios_acreditacion/', views.medio_acreditacion_list, name='medio_acreditacion_list'),
    path('medios_acreditacion/crear/', views.medio_acreditacion_create, name='medio_acreditacion_create'),
    path('medios_acreditacion/editar/<int:pk>/', views.medio_acreditacion_update, name='medio_acreditacion_update'),
    path('medios_acreditacion/toggle/<int:pk>/', views.medio_acreditacion_toggle, name='medio_acreditacion_toggle'),
    path('medios_acreditacion/detalle/<int:pk>/', views.medio_acreditacion_detail, name='medio_acreditacion_detail'),

    path('entidad/<int:entidad_id>/campos/', views.campos_entidad_list, name='campos_entidad_list'),
    path('campo_entidad/<int:campo_id>/editar/', views.campo_entidad_edit, name='campo_entidad_edit'),
    path('campo_entidad/<int:campo_id>/eliminar/', views.campo_entidad_delete, name='campo_entidad_delete'),
    path('entidad/<int:entidad_id>/campos/add/', views.campo_entidad_create, name='campo_entidad_create'),
    path('medios_acreditacion/<int:entidad_id>/<int:cliente_id>/', views.medio_acreditacion_dinamico, name='medio_acreditacion_dinamico'),

]
