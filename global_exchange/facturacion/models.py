from django.db import models
from usuarios.models import CustomUser
from django.forms import ValidationError
from clientes.models import Cliente
from operaciones.models import Transaccion

class RangoFacturacion(models.Model):
    """
    Representa un **rango de numeración autorizado** para emitir facturas electrónicas.

    Cada usuario tiene asignado un rango con un código de **establecimiento**, 
    **punto de expedición** y un bloque de números correlativos.

    Este modelo controla la numeración secuencial y la disponibilidad de números.

    **Atributos:**
        - **establecimiento (str):** Código del establecimiento (3 dígitos).
        - **punto_expedicion (str):** Código del punto de expedición (3 dígitos).
        - **numero_inicio (int):** Primer número del rango.
        - **numero_fin (int):** Último número del rango.
        - **numero_actual (int):** Número que se usará en la siguiente factura.
        - **usuario (CustomUser):** Usuario al que pertenece el rango.
        - **activo (bool):** Indica si el rango está activo.
        - **fecha_asignacion (datetime):** Fecha de creación o asignación del rango.
    """
    establecimiento = models.CharField(max_length=3, default="001")
    punto_expedicion = models.CharField(max_length=3, default="003")
    
    numero_inicio = models.IntegerField()
    numero_fin = models.IntegerField()
    numero_actual = models.IntegerField()
    
    # Relación con usuario o equipo
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['establecimiento', 'punto_expedicion', 'numero_inicio']
        ordering = ['establecimiento', 'punto_expedicion', 'numero_inicio']
    
    def __str__(self):
        return f"{self.establecimiento}-{self.punto_expedicion} ({self.numero_inicio} a {self.numero_fin})"
    
    def clean(self):
        if self.numero_inicio > self.numero_fin:
            raise ValidationError("El número inicial no puede ser mayor al final")
        
        if self.numero_actual < self.numero_inicio or self.numero_actual > self.numero_fin:
            raise ValidationError("El número actual debe estar dentro del rango")
    
    def obtener_siguiente_numero(self):
        """
        Obtiene el siguiente número disponible y actualiza el contador del rango.

        **Retorna:**
            - **str:** Número de factura formateado a 7 dígitos (por ejemplo `'0000123'`).

        **Lanza:**
            - **ValidationError:** Si el rango está agotado.
        """
        # CORRECCIÓN: Verificar ANTES de usar el número
        if self.numero_actual > self.numero_fin:
            raise ValidationError(f"Rango agotado. Límite: {self.numero_fin}")
        
        # Guardar el número actual para usarlo
        numero_a_usar = self.numero_actual
        
        # Incrementar para la próxima factura
        self.numero_actual += 1
        self.save()
        
        # Retornar el número formateado que REALMENTE se usó
        return self._formatear_numero(numero_a_usar)
    
    def _formatear_numero(self, numero):
        """
        Formatea un número a 7 dígitos con ceros a la izquierda.

        **Parámetros:**
            - **numero (int):** Número a formatear.

        **Retorna:**
            - **str:** Número con formato `'0000001'`.
        """
        return str(numero).zfill(7)
    
    @property
    def numeros_disponibles(self):
        """
        Devuelve la cantidad de números restantes en el rango.

        **Retorna:**
            - **int:** Números aún disponibles.
        """
        return self.numero_fin - self.numero_actual + 1
    
    @property
    def porcentaje_usado(self):
        """
        Calcula el porcentaje del rango ya utilizado.

        **Retorna:**
            - **float:** Porcentaje de uso del rango.
        """
        total = self.numero_fin - self.numero_inicio + 1
        usado = self.numero_actual - self.numero_inicio
        return (usado / total) * 100 if total > 0 else 0


class Factura(models.Model):
    """
    Representa una **factura electrónica** generada dentro del sistema.

    Cada factura tiene un número único compuesto por:

    ```
    establecimiento-punto_expedicion-numero_documento
    ```

    Además, almacena el CDC, estado reportado por **SIFEN**, archivos asociados 
    (PDF/XML) y la relación con la **transacción** y el **rango de facturación** 
    que la originaron.

    **Atributos:**
        - **numero (str):** Número completo de factura (`001-003-0000001`).
        - **cdc (str):** Código de control generado por Factura Segura.
        - **cliente (Cliente):** Cliente receptor de la factura.
        - **transaccion (Transaccion):** Transacción asociada.
        - **monto_total (Decimal):** Importe total facturado.
        - **moneda (str):** Moneda utilizada (ej: `'PYG'`, `'USD'`).
        - **tipo_cambio (Decimal):** Tasa de cambio aplicada.
        - **estado (str):** Estado interno (`pendiente`, `aprobado`, etc.).
        - **estado_sifen (str):** Estado retornado por SIFEN.
        - **descripcion_sifen (str):** Mensaje detallado del estado SIFEN.
        - **fecha_emision (datetime):** Fecha de emisión.
        - **fecha_aprobacion (datetime):** Fecha de aprobación.
        - **json_factura (dict):** Representación JSON del documento.
        - **operation_id (str):** ID de operación devuelto por FacturaSegura.
        - **archivo_kude (File):** PDF del KuDE.
        - **archivo_xml (File):** Archivo XML del documento electrónico.
        - **creado_por (CustomUser):** Usuario que emitió la factura.
        - **rango_utilizado (RangoFacturacion):** Rango desde el cual se generó el número.
        - **establecimiento (str):** Código del establecimiento.
        - **punto_expedicion (str):** Código del punto de expedición.
        - **numero_documento (str):** Número correlativo (7 dígitos).
    """
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
    ]
    numero = models.CharField(max_length=20, unique=True)  # Aumentado para 001-003-0000001
    cdc = models.CharField(max_length=44, unique=True, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    transaccion = models.OneToOneField(Transaccion, on_delete=models.PROTECT)
    
    monto_total = models.DecimalField(max_digits=15, decimal_places=2)
    moneda = models.CharField(max_length=10)
    tipo_cambio = models.DecimalField(max_digits=10, decimal_places=4)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    estado_sifen = models.CharField(max_length=50, null=True, blank=True)
    descripcion_sifen = models.TextField(null=True, blank=True)
    
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    
    json_factura = models.JSONField(null=True, blank=True)
    operation_id = models.CharField(max_length=50, null=True, blank=True)
    
    archivo_kude = models.FileField(upload_to='facturas/kude/', null=True, blank=True)
    archivo_xml = models.FileField(upload_to='facturas/xml/', null=True, blank=True)
    
    creado_por = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    
    rango_utilizado = models.ForeignKey(
        RangoFacturacion, 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    establecimiento = models.CharField(max_length=3)
    punto_expedicion = models.CharField(max_length=3)
    numero_documento = models.CharField(max_length=7)

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para autogenerar el número completo
        si aún no fue definido antes de guardar el registro.
        """
        if not self.numero:
            self.numero = f"{self.establecimiento}-{self.punto_expedicion}-{self.numero_documento}"
        super().save(*args, **kwargs)

    @property
    def numero_completo(self):
        """
        Devuelve el número completo de la factura (formato estándar).

        Returns:
            str: Ejemplo: '001-003-0000101'.
        """
        return self.numero
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero} - {self.cdc}"