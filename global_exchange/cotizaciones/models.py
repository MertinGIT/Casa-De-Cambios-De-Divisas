from django.db import models
from monedas.models import Moneda

class TasaDeCambio(models.Model):
    moneda_origen = models.ForeignKey(
        Moneda,
        related_name="tasas_origen",
        on_delete=models.CASCADE
    )
    moneda_destino = models.ForeignKey(
        Moneda,
        related_name="tasas_destino",
        on_delete=models.CASCADE
    )
    monto_compra = models.DecimalField(max_digits=23, decimal_places=8)
    monto_venta = models.DecimalField(max_digits=23, decimal_places=8)
    vigencia = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ["-fecha_actualizacion"]
    

    def __str__(self):
        return f"{self.moneda_origen}/{self.moneda_destino} - Compra: {self.monto_compra} Venta: {self.monto_venta}"
