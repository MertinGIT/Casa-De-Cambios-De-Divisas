from django.db import models
from django.core.exceptions import ValidationError

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
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='limites_transaccion',
        help_text="Cliente al que se le asigna este límite de transacción"
    )
    moneda = models.ForeignKey(
        'monedas.Moneda',
        on_delete=models.CASCADE,
        related_name='limites_transaccion',
        help_text="Moneda para la cual se establece el límite"
    )
    limite_diario = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Monto máximo permitido por día"
    )
    limite_mensual = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Monto máximo permitido por mes"
    )
    estado = models.CharField(
        max_length=10,
        default='activo',
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        help_text="Estado del límite de transacción"
    )

    class Meta:
        verbose_name = "Límite de Transacción"
        verbose_name_plural = "Límites de Transacción"

    def __str__(self):
        """Representación legible: 'Cliente - Moneda'"""
        return f"{self.cliente.nombre} - {self.moneda.nombre}"

    def clean(self):
        if self.limite_mensual < self.limite_diario:
            raise ValidationError("El límite mensual no puede ser menor al límite diario.")

        # Si este límite está activo, no puede haber otro activo para el mismo cliente/moneda
        if self.estado == 'activo':
            qs = LimiteTransaccion.objects.filter(
                cliente=self.cliente,
                moneda=self.moneda,
                estado='activo'
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Este cliente ya tiene un límite activo para esta moneda.")


    def save(self, *args, **kwargs):
        """Aplicar validaciones antes de guardar"""
        self.clean()
        super().save(*args, **kwargs)
