from django.db import models

# Create your models here.
# ============================================
# models.py - Agregar estos modelos
# ============================================
from django.db import models
from monedas.models import Moneda
from decimal import Decimal


class Denominacion(models.Model):
    """
    Representa las denominaciones disponibles para cada moneda.
    Ejemplo: Para USD pueden ser 1, 5, 10, 20, 50, 100
    Para PYG pueden ser 2000, 5000, 10000, 20000, 50000, 100000
    """
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name='denominaciones'
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Valor de la denominación (ej: 100 para billete de 100)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está activo para uso en TAUSER"
    )
    
    class Meta:
        ordering = ['-valor']
        unique_together = ['moneda', 'valor']
        verbose_name = "Denominación"
        verbose_name_plural = "Denominaciones"
    
    def __str__(self):
        return f"{self.moneda.abreviacion} {self.valor}"


class StockTauser(models.Model):
    """
    Stock de billetes por denominación en el TAUSER.
    Controla cuántos billetes de cada denominación hay disponibles.
    """
    denominacion = models.OneToOneField(
        Denominacion,
        on_delete=models.CASCADE,
        related_name='stock'
    )
    cantidad = models.IntegerField(
        default=0,
        help_text="Cantidad de billetes disponibles"
    )
    cantidad_minima = models.IntegerField(
        default=10,
        help_text="Alerta cuando el stock sea menor a este valor"
    )
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stock TAUSER"
        verbose_name_plural = "Stock TAUSER"
    
    def __str__(self):
        return f"{self.denominacion} - Stock: {self.cantidad}"
    
    @property
    def stock_bajo(self):
        """Retorna True si el stock está por debajo del mínimo"""
        return self.cantidad < self.cantidad_minima
    
    @property
    def valor_total(self):
        """Calcula el valor total de esta denominación en stock"""
        return self.denominacion.valor * self.cantidad


class MovimientoStock(models.Model):
    """
    Historial de movimientos de stock del TAUSER.
    Registra cargas (aprovisionar) y retiros de billetes.
    """
    TIPO_MOVIMIENTO = [
        ('carga', 'Carga/Aprovisionamiento'),
        ('retiro', 'Retiro'),
        ('ajuste', 'Ajuste Manual'),
    ]
    
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField(
        help_text="Cantidad de billetes (positivo para carga, negativo para retiro)"
    )
    stock_anterior = models.IntegerField()
    stock_posterior = models.IntegerField()
    transaccion = models.ForeignKey(
        'operaciones.Transaccion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_stock',
        help_text="Transacción asociada si es un retiro de cliente"
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
    
    def __str__(self):
        return f"{self.tipo.upper()} - {self.denominacion} x{abs(self.cantidad)}"


class RetiroEfectivo(models.Model):
    """
    Detalle de cómo se entregó el efectivo en una transacción.
    Guarda qué denominaciones y cantidades se usaron.
    """
    transaccion = models.OneToOneField(
        'operaciones.Transaccion',
        on_delete=models.CASCADE,
        related_name='retiro_efectivo'
    )
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    monto_entregado = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Monto real entregado (puede ser menor por falta de denominaciones pequeñas)"
    )
    diferencia = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        help_text="Diferencia no entregada (resto que no se pudo dar)"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia')],
        default='efectivo'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Retiro en Efectivo"
        verbose_name_plural = "Retiros en Efectivo"
    
    def __str__(self):
        return f"Retiro {self.transaccion.id} - {self.monto_entregado} {self.transaccion.moneda_destino}"


class DetalleRetiroEfectivo(models.Model):
    """
    Detalle de las denominaciones usadas en un retiro específico.
    Ejemplo: 7 billetes de 100, 1 billete de 20, etc.
    """
    retiro = models.ForeignKey(
        RetiroEfectivo,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.CASCADE
    )
    cantidad = models.IntegerField(help_text="Cantidad de billetes entregados")
    
    class Meta:
        verbose_name = "Detalle de Retiro"
        verbose_name_plural = "Detalles de Retiro"
    
    def __str__(self):
        return f"{self.cantidad}x {self.denominacion}"
    
    @property
    def subtotal(self):
        return self.denominacion.valor * self.cantidad

class ReservaTauser(models.Model):
    """
    Representa una reserva temporal de efectivo en el TAUSER para una transacción en proceso.
    No descuenta del stock real hasta que se confirma.
    """
    transaccion = models.OneToOneField(
        'operaciones.Transaccion',
        on_delete=models.CASCADE,
        related_name='reserva_tauser'
    )
    moneda = models.ForeignKey('monedas.Moneda', on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)
    expiracion = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha/hora en la que expira la reserva (opcional)"
    )
    activa = models.BooleanField(default=True)


class DetalleReservaTauser(models.Model):
    reserva = models.ForeignKey(
        ReservaTauser,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    denominacion = models.ForeignKey(Denominacion, on_delete=models.CASCADE)
    cantidad_reservada = models.IntegerField()

