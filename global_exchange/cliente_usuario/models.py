# usuarios/models.py
from usuarios.models import CustomUser
from django.db import models 


class Usuario_Cliente(models.Model):
    """
    Modelo intermedio que representa la asignación entre un usuario y un cliente.

    Campos:
        - ``id_usuario``: referencia al usuario (``CustomUser``).
        - ``id_cliente``: referencia al cliente asociado.

    Notas:
        - Cada fila de esta tabla indica que un usuario tiene relación con un cliente específico.
    """
    id_usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="usuario_clientes"
    )
    id_cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name="cliente_usuarios"
    )

    class Meta:
        db_table = "usuario_cliente" 
        verbose_name = "Usuario Cliente"
        verbose_name_plural = "Usuarios Clientes"

    def __str__(self):
        """Devuelve una representación legible de la asignación."""
        return f"{self.id_usuario.username} - {self.id_cliente.nombre}"