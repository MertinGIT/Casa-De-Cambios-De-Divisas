# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from roles_permisos.models import Rol

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema Global Exchange.

    Hereda de `AbstractUser` y agrega campos específicos del proyecto.

    Atributos:
        username (str): Nombre de usuario único (heredado de AbstractUser).
        email (str): Correo electrónico del usuario (heredado).
        cedula (str): Número de cédula único del usuario.
        rol (Rol): Relación con el rol del usuario, permite definir permisos y tipo de usuario.

    Métodos:
        __str__(): Retorna el nombre de usuario como representación del objeto.
    """
    
    # Eliminamos first_name y last_name si no los vamos a usar
    first_name = None
    last_name = None
    # Nuevo campo
    cedula = models.CharField(max_length=20, unique=True, null=False, blank=False)

    # Relación con Rol
    rol = models.ForeignKey("roles_permisos.Rol", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios")


    def __str__(self):
        """Retorna el nombre de usuario como string representativo."""
        return self.username
