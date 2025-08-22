# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from roles_permisos.models import Rol

class CustomUser(AbstractUser):
    # Eliminamos first_name y last_name si no los vamos a usar
    first_name = None
    last_name = None
    # Nuevo campo
    cedula = models.CharField(max_length=20, unique=True, null=False, blank=False)

    # Relación con Rol
    rol = models.ForeignKey("roles_permisos.Rol", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios")


    def __str__(self):
        return self.username
