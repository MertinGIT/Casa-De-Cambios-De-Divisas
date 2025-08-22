from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Usuario_Rol_Cliente(models.Model):
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
        return f"{self.id_usuario.username} - {self.id_cliente.nombre}"
