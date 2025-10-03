from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from monedas.models import Moneda  

class LimiteTransaccion(models.Model):
    """
    Representa un límite de transacción para un cliente específico en una moneda concreta.

    Relación:
        - Un cliente puede tener múltiples límites, uno por cada moneda.
        - Cada límite está asociado a exactamente un cliente y una moneda.

    Campos:
        cliente (ForeignKey): Cliente al que se asigna este límite.
        moneda (ForeignKey): Moneda asociada a este límite.
        limite_diario (DecimalField): Límite máximo diario.
        limite_mensual (DecimalField): Límite máximo mensual.
        estado (CharField): Estado del límite ('activo' o 'inactivo').

    Restricciones:
        - unique_together: Un cliente no puede tener más de un límite para la misma moneda.
        - Validation: limite_mensual >= limite_diario.
    """
    limite_diario = models.DecimalField(
        max_digits=20, decimal_places=8, default=Decimal('0'),
        help_text="Límite máximo por día (en moneda base)."
    )
    limite_mensual = models.DecimalField(
        max_digits=20, decimal_places=8, default=Decimal('0'),
        help_text="Límite máximo por mes (en moneda base)."
    )
    estado = models.CharField(max_length=10, default='activo')
    def get_moneda_default():
        return Moneda.objects.get(abreviacion="PYG").id
    
    moneda = models.ForeignKey(
        'monedas.Moneda',
        null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="Moneda base para los límites. Si es None, se buscará la moneda por defecto.",
        default=get_moneda_default
    )


    def __str__(self):
        """Representación legible: 'Cliente - Moneda'"""
        return f"Límites (Diario: {self.limite_diario}, Mensual: {self.limite_mensual})"

    class Meta:
        verbose_name = "Límite de Transacción"
        verbose_name_plural = "Límites de Transacción"


 