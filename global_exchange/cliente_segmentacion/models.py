from django.db import models

class Segmentacion(models.Model):
    """
    Representa la segmentación de clientes según criterios de negocio.

    Cada segmentación permite aplicar descuentos específicos a un grupo de clientes.

    Campos:
        nombre (CharField): Nombre único de la segmentación (máx. 50 caracteres).
        descripcion (TextField): Descripción opcional de la segmentación.
        descuento (DecimalField): Porcentaje de descuento asociado a la segmentación.
        estado (CharField): Estado de la segmentación ('activo' o 'inactivo').

    Propiedades:
        descuento_aplicable: Devuelve 0 si la segmentación está inactiva, 
        de lo contrario retorna el valor real del descuento.
    """
    nombre = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nombre único de la segmentación"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción opcional de la segmentación"
    )
    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Descuento en porcentaje para este tipo de cliente"
    )
    estado = models.CharField(
        max_length=10,
        default='activo',
        help_text="Estado de la segmentación (activo/inactivo)"
    )

    @property
    def descuento_aplicable(self):
        """
        Retorna el descuento aplicable según el estado de la segmentación.

        Devuelve:
            Decimal: 0 si el estado es 'inactivo', de lo contrario el valor real del descuento.
        """
        return 0 if self.estado == "inactivo" else self.descuento

    def __str__(self):
        """Representación legible del objeto"""
        return self.nombre
