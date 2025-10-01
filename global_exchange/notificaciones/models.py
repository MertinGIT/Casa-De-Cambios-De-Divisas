from django.db import models
from django.conf import settings  # para referenciar al usuario
from monedas.models import Moneda  # asumo que tu modelo de monedas está en 'operaciones'


class NotificacionMoneda(models.Model):
    """
    Relaciona un usuario con una moneda para configurar notificaciones personalizadas.

    - user: el usuario dueño de la configuración
    - moneda: la moneda que quiere seguir
    - activa: si la notificación está habilitada o no
    - creado / actualizado: timestamps
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "moneda")  # evita duplicados
        verbose_name = "Notificación de Moneda"
        verbose_name_plural = "Notificaciones de Monedas"

    def __str__(self):
        return f"{self.user.username} → {self.moneda.abreviacion}"
