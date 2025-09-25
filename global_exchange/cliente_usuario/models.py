from usuarios.models import CustomUser
from django.db import models

class Usuario_Cliente(models.Model):
    """
    Modelo intermedio que representa la asignación entre un usuario y un cliente.

    :cvar id_usuario: Referencia al usuario asociado.
    :type id_usuario: ForeignKey[:class:`usuarios.models.CustomUser`]

    :cvar id_cliente: Referencia al cliente asociado.
    :type id_cliente: ForeignKey[:class:`clientes.models.Cliente`]

    :cvar Meta.db_table: Nombre de la tabla en la base de datos.
    :type Meta.db_table: str
    :cvar Meta.verbose_name: Nombre legible de la entidad.
    :type Meta.verbose_name: str
    :cvar Meta.verbose_name_plural: Nombre plural legible.
    :type Meta.verbose_name_plural: str

    Notas
    -----
    - Cada fila de esta tabla indica que un usuario tiene relación con un cliente específico.
    - Sirve como tabla intermedia para relaciones Many-to-Many entre usuarios y clientes.
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
        """
        Devuelve una representación legible de la asignación.

        :return: Cadena en formato "usuario - cliente".
        :rtype: str
        """
        return f"{self.id_usuario.username} - {self.id_cliente.nombre}"
