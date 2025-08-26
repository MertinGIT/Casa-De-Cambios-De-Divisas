from django.db import models
class Segmentacion(models.Model):
    """
    Modelo que representa la segmentación de clientes según criterios de negocio.

    Campos:
        - ``nombre`` (CharField): Nombre único de la segmentación (máx. 50 caracteres).
        - ``descripcion`` (TextField): Descripción opcional que detalla la segmentación.
        - ``descuento`` (DecimalField): Porcentaje de descuento asociado a la segmentación.

    Notas:
        - Este modelo permite clasificar a los clientes en grupos (segmentos) con descuentos específicos.
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Descuento en porcentaje para este tipo de cliente"
    )
    
class Cliente(models.Model):
    """
    Modelo que representa a los clientes registrados en el sistema.

    Campos:
        - ``nombre`` (CharField): Nombre completo del cliente (máx. 150 caracteres).
        - ``email`` (EmailField): Correo electrónico único del cliente.
        - ``telefono`` (CharField): Número de teléfono del cliente (opcional, máx. 20 caracteres).
        - ``segmentacion`` (ForeignKey): Segmentación a la que pertenece el cliente.
        - ``estado`` (CharField): Estado del cliente (activo por defecto).
        - ``creado_en`` (DateTimeField): Fecha de creación (asignada automáticamente).
        - ``actualizado_en`` (DateTimeField): Fecha de última actualización (automática).

    Notas:
        - El campo ``segmentacion`` protege la integridad: no se puede eliminar un segmento si está asociado a un cliente.
    """
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    segmentacion = models.ForeignKey(Segmentacion, on_delete=models.PROTECT)
    estado = models.CharField(max_length=10, default='activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
