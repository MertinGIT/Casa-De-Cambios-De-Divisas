from django.db import models
from clientes.models import Cliente

class TipoEntidadFinanciera(models.Model):
    """
    Representa una entidad financiera disponible en el sistema.

    Campos:
        - nombre (str): Nombre de la entidad financiera (ej. "Banco Itaú", "Tigo Money").
        - tipo (str): Tipo de entidad, con opciones: BANCO, BILLETERA, COOPERATIVA, FINTECH, OTRO.
        - estado (bool): Indica si la entidad está activa o inactiva.
        - comision (Decimal): Comisión que gana la entidad por transacción.
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
    comision = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Comisión que gana la entidad por transacción")

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
    Ahora solo almacena la relación con cliente, entidad y estado.
    Los datos específicos se guardan en ValorCampoMedioAcreditacion.
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='medios_acreditacion')
    entidad = models.ForeignKey(TipoEntidadFinanciera, on_delete=models.CASCADE)
    
    # Estado y metadatos
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Medio de Acreditación"
        verbose_name_plural = "Medios de Acreditación"

    def __str__(self):
        """
        Retorna una representación legible del medio de acreditación.

        :return: String con formato "Cliente - Entidad (ID)".
        """
        return f"{self.cliente.nombre} - {self.entidad.nombre} (ID: {self.id})"

    @property
    def dynamic_fields(self):
        """
        Retorna una lista de diccionarios con los campos dinámicos: [{
            'label': campo.etiqueta,
            'value': valor.valor,
            'campo': campo,
            'valor_obj': valor
        }, ...]
        """
        valores = self.valores_campos.select_related('campo').all()
        return [
            {
                'label': v.campo.etiqueta,
                'value': v.valor,
                'campo': v.campo,
                'valor_obj': v
            }
            for v in valores
        ]


class CampoEntidadFinanciera(models.Model):
    """
    Define los campos requeridos por cada entidad financiera para el alta de un medio de acreditación.
    """
    entidad = models.ForeignKey(TipoEntidadFinanciera, on_delete=models.CASCADE, related_name='campos')
    nombre = models.CharField(max_length=100)  # Ej: "cedula", "telefono"
    etiqueta = models.CharField(max_length=100)  # Ej: "Cédula de Identidad"
    tipo = models.CharField(max_length=20, choices=[
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('fecha', 'Fecha'),
        ('email', 'Email'),
    ])
    requerido = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    regex_validacion = models.CharField(max_length=255, blank=True)
    mensaje_error = models.CharField(max_length=255, blank=True)
    placeholder = models.CharField(max_length=100, blank=True)
    ayuda = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.entidad.nombre} - {self.etiqueta}"


class ValorCampoMedioAcreditacion(models.Model):
    """
    Almacena el valor ingresado por el usuario para cada campo dinámico de un medio de acreditación.
    """
    medio = models.ForeignKey(MedioAcreditacion, on_delete=models.CASCADE, related_name='valores_campos')
    campo = models.ForeignKey(CampoEntidadFinanciera, on_delete=models.CASCADE)
    valor = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.medio} - {self.campo.etiqueta}: {self.valor}"