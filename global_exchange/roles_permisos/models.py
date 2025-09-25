from django.db import models
from django.contrib.auth.models import Group


class GroupProfile(models.Model):
    """
    Extiende el modelo :class:`django.contrib.auth.models.Group` con información adicional.

    Esta clase crea un perfil asociado a cada grupo del sistema, permitiendo
    registrar el estado del grupo.

    Attributes
    ----------
    group : OneToOneField
        Relación uno a uno con :class:`django.contrib.auth.models.Group`.  
        Cada grupo tiene exactamente un perfil asociado.
    estado : CharField
        Estado actual del grupo. Puede ser ``Activo`` o ``Inactivo``.
    """

    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    estado = models.CharField(
        max_length=10,
        choices=[("Activo", "Activo"), ("Inactivo", "Inactivo")],
        default="Activo",
    )

    def __str__(self) -> str:
        """
        Representación legible del perfil de grupo.

        Returns
        -------
        str
            Una cadena con el nombre del grupo y su estado.
        """
        return f"{self.group.name} ({self.estado})"
