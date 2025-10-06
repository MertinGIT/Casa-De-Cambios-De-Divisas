from django.urls import path
from . import views
from medio_acreditacion.views import medio_acreditacion_dinamico
urlpatterns = [
    # CRUD de usuarios con roles y permisos
    path("usuarios-roles/", views.user_roles_lista, name="user_roles_lista"),
    path("usuarios-roles/editar/<int:pk>/", views.user_roles_edit, name="user_roles_edit"),
    path("usuarios-roles/detalle/<int:pk>/", views.user_roles_detalle, name="user_roles_detalle"),
    path('api/login/', views.login_api, name='login_api'),
]
