from django.db import models
from clientes.models import Cliente
from monedas.models import Moneda
class TipoEntidadFinanciera(models.Model):
    """Catálogo de entidades financieras disponibles"""
    nombre = models.CharField(max_length=100)  # "Banco Itaú", "Tigo Money", etc.
    tipo = models.CharField(max_length=20, choices=[
        ('BANCO', 'Banco'),
        ('BILLETERA', 'Billetera Digital'),
        ('COOPERATIVA', 'Cooperativa'),
        ('FINTECH', 'Fintech'),
        ('OTRO', 'Otro')
    ])
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Entidad Financiera"
        verbose_name_plural = "Tipos de Entidades Financieras"

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class MedioAcreditacion(models.Model):
    """Medios de acreditación que tiene cada cliente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='medios_acreditacion')
    entidad = models.ForeignKey(TipoEntidadFinanciera, on_delete=models.CASCADE)
    
    # Información de la cuenta/medio
    numero_cuenta = models.CharField(max_length=50, help_text="Número de cuenta, teléfono o identificador")
    tipo_cuenta = models.CharField(max_length=20, choices=[
        ('AHORRO', 'Cuenta de Ahorro'),
        ('CORRIENTE', 'Cuenta Corriente'),
        ('BILLETERA', 'Billetera Digital'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('OTRO', 'Otro')
    ])
    
    # Información del titular
    titular = models.CharField(max_length=200, help_text="Nombre del titular de la cuenta")
    documento_titular = models.CharField(max_length=20, blank=True, help_text="CI/RUC del titular")
    
    # Configuración
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE)
    
    # Estado y metadatos
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Medio de Acreditación"
        verbose_name_plural = "Medios de Acreditación"
        unique_together = ['entidad', 'numero_cuenta']

    def __str__(self):
        return f"{self.cliente.nombre} - {self.entidad.nombre} ({self.numero_cuenta})"

    @property
    def identificador_completo(self):
        """Retorna un identificador completo para usar con el sistema bancario"""
        return f"{self.entidad.codigo}_{self.numero_cuenta}"
