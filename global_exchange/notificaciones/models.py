from django.db import models
from django.conf import settings  # para referenciar al usuario
from cotizaciones.models import TasaDeCambio
from monedas.models import Moneda  # asumo que tu modelo de monedas está en 'operaciones'


class NotificacionMoneda(models.Model):
    """
    Configuración individual de notificaciones de cambio de tasas para un usuario.

    Esta tabla asocia a cada usuario con las monedas sobre las que desea recibir
    notificaciones en tiempo real cuando se actualicen sus tasas de cambio.

    Atributos:
        user (ForeignKey): Usuario dueño de la configuración.
        moneda (ForeignKey): Moneda a la cual se le quiere hacer seguimiento.
        activa (bool): Indica si la notificación está habilitada.
        creado (datetime): Fecha de creación del registro.
        actualizado (datetime): Última vez que se modificó la configuración.

    Restricciones:
        unique_together = (user, moneda): Evita duplicar configuraciones para la misma moneda.
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
    Registro histórico de cambios realizados sobre las tasas de cambio.

    Cada vez que se crea o modifica una tasa, se genera un registro de auditoría
    que almacena los valores anteriores y los nuevos, junto con la fecha, tipo
    de cambio y usuario responsable.

    Atributos:
        tasa (ForeignKey): Referencia a la tasa modificada.
        tipo_cambio (str): Indica si fue creación, edición o desactivación.
        precio_anterior (Decimal): Valor previo de la tasa antes del cambio.
        vigencia_anterior (date): Fecha de vigencia anterior.
        estado_anterior (bool): Estado anterior de la tasa.
        precio_nuevo (Decimal): Valor actualizado de la tasa.
        vigencia_nueva (date): Nueva fecha de vigencia.
        estado_nuevo (bool): Nuevo estado de la tasa.
        usuario_cambio (ForeignKey): Usuario que realizó la modificación (opcional).
        fecha_cambio (datetime): Fecha en que se registró el cambio.
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
        """Devuelve una representación legible del registro de auditoría."""
        return f"{self.tipo_cambio} - {self.tasa.moneda_origen.abreviacion} ({self.fecha_cambio})"
    
    def porcentaje_cambio(self):
        """
        Calcula el porcentaje de variación entre el precio anterior y el nuevo.
        
        Retorna:
            float: Valor absoluto del cambio porcentual (0 si no hay valor anterior).
        """
        if self.precio_anterior and self.precio_anterior > 0:
            return abs((self.precio_nuevo - self.precio_anterior) / self.precio_anterior * 100)
        return 0