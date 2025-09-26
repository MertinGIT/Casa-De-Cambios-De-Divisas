from django.db import models
from clientes.models import Cliente
from monedas.models import Moneda

class TipoEntidadFinanciera(models.Model):
    """
    Representa una entidad financiera disponible en el sistema.

    Campos:
        - nombre (str): Nombre de la entidad financiera (ej. "Banco Itaú", "Tigo Money").
        - tipo (str): Tipo de entidad, con opciones: BANCO, BILLETERA, COOPERATIVA, FINTECH, OTRO.
        - estado (bool): Indica si la entidad está activa o inactiva.

    Métodos:
        - __str__: Retorna una representación legible de la entidad.
    """
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
        """
        Retorna una representación legible de la entidad financiera.

        :return: String con formato "Nombre (Tipo)".
        """
        return f"{self.nombre} ({self.tipo})"


class MedioAcreditacion(models.Model):
    """
    Representa un medio de acreditación asociado a un cliente.

    Campos:
        - cliente (ForeignKey): Cliente propietario del medio de acreditación.
        - entidad (ForeignKey): Entidad financiera del medio.
        - numero_cuenta (str): Número de cuenta, teléfono o identificador.
        - tipo_cuenta (str): Tipo de cuenta, con opciones como AHORRO, CORRIENTE, BILLETERA, etc.
        - titular (str): Nombre del titular de la cuenta.
        - documento_titular (str): Documento del titular (CI/RUC), opcional.
        - moneda (ForeignKey): Moneda asociada al medio de acreditación.
        - estado (bool): Indica si el medio está activo o inactivo.

    Configuración:
        - unique_together: Asegura que no existan duplicados de entidad + número_cuenta.
    
    Métodos:
        - __str__: Retorna una representación legible del medio de acreditación.
        - identificador_completo: Propiedad que retorna un identificador completo para el sistema bancario.
    """
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
        """
        Retorna una representación legible del medio de acreditación.

        :return: String con formato "Cliente - Entidad (Número de cuenta)".
        """
        return f"{self.cliente.nombre} - {self.entidad.nombre} ({self.numero_cuenta})"

    @property
    def identificador_completo(self):
        """
        Genera un identificador completo del medio de acreditación.

        Se puede usar para integrar con sistemas bancarios u otros procesos internos.

        :return: String con formato "codigoEntidad_numeroCuenta".
        """
        return f"{self.entidad.codigo}_{self.numero_cuenta}"