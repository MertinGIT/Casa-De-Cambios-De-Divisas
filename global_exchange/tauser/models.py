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
    Representa las denominaciones de billetes o monedas disponibles para cada tipo de moneda.

    **Ejemplos:**

    - USD → 1, 5, 10, 20, 50, 100  
    - PYG → 2000, 5000, 10000, 20000, 50000, 100000  

    **Atributos:**

    - **moneda (ForeignKey):**  
      Referencia a la moneda a la que pertenece la denominación.

    - **valor (DecimalField):**  
      Valor del billete o moneda.

    - **activo (BooleanField):**  
      Indica si la denominación está habilitada para operaciones.
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

class Localidad(models.Model):
    """
    Representa una ubicación física de un TAUSER (terminal de autoservicio).

    **Atributos:**

    - **nombre (CharField):**  
      Nombre de la localidad (único).

    - **direccion (CharField):**  
      Dirección física (opcional).

    - **activo (BooleanField):**  
      Indica si la localidad está activa.
    """
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
    
    def __str__(self):
        return self.nombre
    
class StockTauser(models.Model):
    """
    Controla el stock de billetes por denominación en el TAUSER.

    Cada localidad mantiene su propio stock independiente para cada denominación.
    Se utiliza para verificar disponibilidad antes de retiros y registrar depósitos.

    **Atributos:**

    - **localidad (ForeignKey):**  
      Localidad donde se encuentra el stock.

    - **denominacion (ForeignKey):**  
      Denominación del billete.

    - **cantidad (IntegerField):**  
      Cantidad actual disponible.

    - **cantidad_minima (IntegerField):**  
      Umbral mínimo de alerta.

    - **actualizado_en (DateTimeField):**  
      Última fecha de actualización.
    """
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    denominacion = models.ForeignKey(
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
        unique_together = ['localidad', 'denominacion']
    
    def __str__(self):
        return f"{self.localidad.nombre} - {self.denominacion} - Stock: {self.cantidad}"
    
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

    Registra toda modificación de stock: cargas, retiros o ajustes manuales.  
    Permite auditoría y trazabilidad de los cambios.

    **Atributos:**

    - **denominacion (ForeignKey):**  
      Denominación afectada.

    - **tipo (CharField):**  
      Tipo de movimiento (`"carga"`, `"retiro"` o `"ajuste"`).

    - **cantidad (IntegerField):**  
      Cantidad movida (positiva o negativa).

    - **stock_anterior (IntegerField):**  
      Cantidad antes del movimiento.

    - **stock_posterior (IntegerField):**  
      Cantidad después del movimiento.

    - **transaccion (ForeignKey):**  
      Transacción asociada (si aplica).

    - **observaciones (TextField):**  
      Detalle o motivo del movimiento.

    - **fecha (DateTimeField):**  
      Fecha del registro.
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
    Registra un retiro de efectivo realizado en una transacción.

    Guarda la información del monto solicitado, monto efectivamente entregado y las posibles
    diferencias debido a disponibilidad limitada de billetes.

    **Atributos:**

    - **transaccion (OneToOneField):**  
      Transacción asociada.

    - **localidad (ForeignKey):**  
      Localidad del TAUSER donde se realiza el retiro.

    - **monto_total (DecimalField):**  
      Monto solicitado por el cliente.

    - **monto_entregado (DecimalField):**  
      Monto realmente entregado.

    - **diferencia (DecimalField):**  
      Monto no entregado (si no se pudieron cubrir todas las denominaciones).

    - **metodo_pago (CharField):**  
      Medio de entrega (`"efectivo"` o `"transferencia"`).

    - **fecha (DateTimeField):**  
      Fecha de ejecución del retiro.
    """
    transaccion = models.OneToOneField(
        'operaciones.Transaccion',
        on_delete=models.CASCADE,
        related_name='retiro_efectivo'
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.PROTECT,
        related_name='retiros'
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
    Representa las denominaciones utilizadas en un retiro específico.

    Permite registrar cuántos billetes de cada denominación se entregaron.

    **Atributos:**

    - **retiro (ForeignKey):**  
      Retiro de efectivo al que pertenece.

    - **denominacion (ForeignKey):**  
      Denominación de billetes entregados.

    - **cantidad (IntegerField):**  
      Número de billetes entregados.
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
    Reserva temporal de efectivo en un TAUSER para una transacción en proceso.

    Se utiliza cuando una transacción aún no ha sido confirmada.  
    Una vez confirmada o expirada, la reserva se libera o descuenta del stock.

    **Atributos:**

    - **transaccion (OneToOneField):**  
      Transacción asociada.

    - **moneda (ForeignKey):**  
      Moneda de la reserva.

    - **monto_total (DecimalField):**  
      Monto total reservado.

    - **creado_en (DateTimeField):**  
      Fecha de creación.

    - **expiracion (DateTimeField):**  
      Fecha y hora de expiración (opcional).

    - **activa (BooleanField):**  
      Indica si la reserva sigue vigente.
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
    """
    Detalla las denominaciones reservadas en una ReservaTauser.

    **Atributos:**

    - **reserva (ForeignKey):**  
      Reserva a la que pertenece.

    - **denominacion (ForeignKey):**  
      Denominación de billetes reservada.

    - **cantidad_reservada (IntegerField):**  
      Cantidad de billetes reservados.
    """
    reserva = models.ForeignKey(
        ReservaTauser,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    denominacion = models.ForeignKey(Denominacion, on_delete=models.CASCADE)
    cantidad_reservada = models.IntegerField()

