# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_usuarios_roles, name='usuarios_roles_lista'),
    path('crear/', views.crear_usuario_rol, name='usuario_rol_crear'),
    path('editar/<int:id>/', views.editar_usuario_rol, name='usuario_rol_editar'),
    path('eliminar/<int:id>/', views.eliminar_usuario_rol, name='usuario_rol_eliminar'),
]
