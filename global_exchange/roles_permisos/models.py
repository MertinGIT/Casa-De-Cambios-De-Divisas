from django.db import models
from django.contrib.auth import get_user_model

#User = get_user_model()
class Permiso(models.Model):
    """
    Modelo que representa un permiso dentro del sistema.

    Campos:
        - ``nombre`` (CharField): Nombre único del permiso (máx. 50 caracteres).

    Notas:
        - Se utiliza para definir acciones específicas que pueden asignarse a los roles.
    """
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        """Devuelve el nombre del permiso."""
        return self.nombre


class Rol(models.Model):
    """
    Modelo que representa los roles de usuario en el sistema.

    Campos:
        - ``nombre`` (CharField): Nombre único del rol (máx. 50 caracteres).
        - ``descripcion`` (TextField): Descripción opcional del rol.
        - ``permisos`` (ManyToManyField): Conjunto de permisos asociados al rol.

    Notas:
        - Un rol puede tener múltiples permisos asociados.
        - Los roles se asignan a los usuarios para definir su nivel de acceso en el sistema.
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(Permiso, blank=True)
    #usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usuarios", null=True)
    def __str__(self):
        permisos_str = ", ".join([p.nombre for p in self.permisos.all()])
        return f"{self.nombre} {self.descripcion} ({permisos_str})"

