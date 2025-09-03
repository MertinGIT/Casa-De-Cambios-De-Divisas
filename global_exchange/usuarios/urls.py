from django.urls import path
from . import views

urlpatterns = [
    # CRUD de usuarios con roles y permisos
    path("roles/", views.user_roles_lista, name="user_roles_lista"),
    path("roles/editar/<int:pk>/", views.user_roles_edit, name="user_roles_edit"),
    path("roles/detalle/<int:pk>/", views.user_roles_detalle, name="user_roles_detalle"),
    path('set_cliente_operativo/', views.set_cliente_operativo, name='set_cliente_operativo'),

]
