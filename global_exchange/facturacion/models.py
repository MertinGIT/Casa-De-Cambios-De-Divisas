from django.db import models
from usuarios.models import CustomUser
from django.forms import ValidationError
from clientes.models import Cliente
from operaciones.models import Transaccion

class RangoFacturacion(models.Model):
    """
    Modelo para gestionar rangos de facturación por equipo/usuario
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
        Obtiene el siguiente número disponible y lo incrementa
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
        Formatea el número a 7 dígitos con ceros a la izquierda
        """
        return str(numero).zfill(7)
    
    @property
    def numeros_disponibles(self):
        """
        Cantidad de números disponibles en el rango
        """
        return self.numero_fin - self.numero_actual + 1
    
    @property
    def porcentaje_usado(self):
        """
        Porcentaje del rango utilizado
        """
        total = self.numero_fin - self.numero_inicio + 1
        usado = self.numero_actual - self.numero_inicio
        return (usado / total) * 100 if total > 0 else 0


class Factura(models.Model):
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
        Genera automáticamente el número completo antes de guardar
        """
        if not self.numero:
            self.numero = f"{self.establecimiento}-{self.punto_expedicion}-{self.numero_documento}"
        super().save(*args, **kwargs)

    @property
    def numero_completo(self):
        """
        Retorna el número completo de la factura
        Ej: 001-003-0000101
        """
        return self.numero
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero} - {self.cdc}"