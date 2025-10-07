from django.db import models
from django.conf import settings  # para referenciar al usuario
from cotizaciones.models import TasaDeCambio
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


class AuditoriaTasaCambio(models.Model):
    """
    Registra TODOS los cambios en las tasas de cambio para análisis y comparación.
    """
    TIPO_CAMBIO = [
        ('CREACION', 'Creación'),
        ('EDICION', 'Edición'),
        ('DESACTIVACION', 'Desactivación'),
    ]
    
    tasa = models.ForeignKey(
        TasaDeCambio,
        on_delete=models.CASCADE,
        related_name='historial_auditoria'
    )
    tipo_cambio = models.CharField(max_length=20, choices=TIPO_CAMBIO)
    
    # Valores anteriores (antes del cambio)
    precio_anterior = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    vigencia_anterior = models.DateField(null=True, blank=True)
    estado_anterior = models.BooleanField(null=True, blank=True)
    
    # Valores nuevos (después del cambio)
    precio_nuevo = models.DecimalField(max_digits=20, decimal_places=2)
    vigencia_nueva = models.DateField()
    estado_nuevo = models.BooleanField(default=True)
    
    # Metadata
    usuario_cambio = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cambios_tasa'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_cambio']
        verbose_name = "Auditoría de Tasa"
        verbose_name_plural = "Auditorías de Tasas"
        indexes = [
            models.Index(fields=['-fecha_cambio', 'tasa']),
        ]
    
    def __str__(self):
        return f"{self.tipo_cambio} - {self.tasa.moneda_origen.abreviacion} ({self.fecha_cambio})"
    
    def porcentaje_cambio(self):
        """Calcula el % de cambio si hay precio anterior"""
        if self.precio_anterior and self.precio_anterior > 0:
            return abs((self.precio_nuevo - self.precio_anterior) / self.precio_anterior * 100)
        return 0