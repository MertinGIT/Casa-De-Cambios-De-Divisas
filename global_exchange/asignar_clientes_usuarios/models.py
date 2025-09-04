from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Usuario_Rol_Cliente(models.Model):
    """
    Modelo intermedio que representa la asignación entre un usuario y un cliente.

    Campos:
        - ``id_usuario``: referencia al usuario (``CustomUser``).
        - ``id_cliente``: referencia al cliente asociado.

    Notas:
        - Cada fila de esta tabla indica que un usuario tiene relación con un cliente específico.
        - El rol del usuario se guarda directamente en el modelo ``CustomUser``.
    """
    id_usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="usuarios_roles_clientes"
    )
    id_cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name="clientes"
    )

    class Meta:
        db_table = "usuario_rol_cliente"  # Nombre de tabla en la BD
        verbose_name = "Usuario Rol Cliente"
        verbose_name_plural = "Usuarios Roles Clientes"

    def __str__(self):
        """Devuelve una representación legible de la asignación."""
        return f"{self.id_usuario.username} - {self.id_cliente.nombre}"
