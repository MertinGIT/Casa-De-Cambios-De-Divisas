from django.db import models
from cliente_segmentacion.models import Segmentacion
from limite_moneda.models import LimiteTransaccion
from monedas.models import Moneda

class Cliente(models.Model):
    """
    Representa a los clientes registrados en el sistema.

    Este modelo almacena la información básica de los clientes y su relación
    con las segmentaciones definidas. Además, permite vincular clientes con
    usuarios del sistema a través de una relación Many-to-Many intermedia.

    Campos:
        nombre (CharField): Nombre completo del cliente (máx. 150 caracteres).
        cedula (CharField, opcional): Número de cédula o identificación del cliente.
        email (EmailField): Correo electrónico único del cliente.
        telefono (CharField, opcional): Número de teléfono del cliente (máx. 20 caracteres).
        segmentacion (ForeignKey): Segmentación asignada al cliente; protege integridad
                                   al impedir eliminar un segmento asociado.
        estado (CharField): Estado del cliente ('activo' por defecto).
        creado_en (DateTimeField): Fecha y hora de creación (asignada automáticamente).
        actualizado_en (DateTimeField): Fecha y hora de última actualización (automática).
        usuarios (ManyToManyField): Relación con usuarios del sistema a través de
                                    la tabla intermedia 'Usuario_Cliente'.

    Notas:
        - La relación con Segmentacion utiliza `on_delete=models.PROTECT` para proteger la integridad.
        - La relación Many-to-Many con usuarios permite asociar múltiples usuarios a un cliente
          y viceversa mediante la tabla intermedia 'Usuario_Cliente'.
    """
    nombre = models.CharField(max_length=150)
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ruc = models.CharField(max_length=15, unique=True, blank=True, null=True, help_text="RUC del cliente en formato válido (ej: 8001234-6)")
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    segmentacion = models.ForeignKey(Segmentacion, on_delete=models.PROTECT)
    estado = models.CharField(max_length=10, default='activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    usuarios = models.ManyToManyField(
        'usuarios.CustomUser',
        through='cliente_usuario.Usuario_Cliente',
        related_name='clientes'
    )

    def __str__(self):
        return self.nombre


class SaldoCliente(models.Model):
    """
    Saldo disponible de un cliente en cada moneda.
    
    Ejemplo:
        Cliente "Juan" puede tener:
        - 50,000,000 PYG (entero, sin decimales)
        - 10,000.50 USD (con decimales)
        - 5,000.75 EUR (con decimales)
        
    Se actualiza cuando:
        - Deposita en ATM (aumenta)
        - Retira del ATM (disminuye)
        - Usa Tauser como medio de acreditación (aumenta)
    
    Notas:
        - max_digits=25: Permite hasta 25 dígitos totales
        - decimal_places=8: Permite hasta 8 decimales
        - Rango: -99,999,999,999,999,999.99999999 a 99,999,999,999,999,999.99999999
        - Para PYG: almacena 50000000.00 (sin usar decimales)
        - Para USD/EUR: almacena 10000.50000000
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='saldos'
    )
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name='saldos_clientes'
    )
    saldo = models.DecimalField(
        max_digits=25,  # ✅ Total de dígitos (antes y después del punto)
        decimal_places=8,  # ✅ Máximo 8 decimales
        default=0,
        help_text="Saldo disponible del cliente en esta moneda (soporta hasta 25 dígitos totales)"
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cliente', 'moneda')
        verbose_name = 'Saldo de Cliente'
        verbose_name_plural = 'Saldos de Clientes'
        indexes = [
            models.Index(fields=['cliente', 'moneda']),
        ]
    
    def __str__(self):
        # ✅ Mostrar sin decimales si es PYG, con decimales si es otra moneda
        if self.moneda.abreviacion.upper() == 'PYG':
            return f"{self.cliente.nombre} - {int(self.saldo):,} {self.moneda.abreviacion}"
        else:
            return f"{self.cliente.nombre} - {self.saldo:.2f} {self.moneda.abreviacion}"
    
    def saldo_formateado(self):
        """
        Retorna el saldo formateado según el tipo de moneda.
        
        Returns:
            str: Saldo formateado (sin decimales para PYG, con 2 decimales para otras)
        """
        if self.moneda.abreviacion.upper() == 'PYG':
            return f"{int(self.saldo):,}"  # Ejemplo: 50,000,000
        else:
            return f"{float(self.saldo):,.2f}"  # Ejemplo: 10,000.50