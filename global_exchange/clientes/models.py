from django.db import models
from cliente_segmentacion.models import Segmentacion

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

    nombre = models.CharField(
        max_length=150,
        help_text="Nombre completo del cliente"
    )
    cedula = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de cédula o identificación del cliente (opcional)"
    )
    email = models.EmailField(
        unique=True,
        help_text="Correo electrónico único del cliente"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de teléfono del cliente (opcional)"
    )
    segmentacion = models.ForeignKey(
        Segmentacion,
        on_delete=models.PROTECT,
        help_text="Segmentación asignada al cliente; no se puede eliminar si está en uso"
    )
    estado = models.CharField(
        max_length=10,
        default='activo',
        help_text="Estado del cliente (activo/inactivo)"
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del registro"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de última actualización del registro"
    )
    usuarios = models.ManyToManyField(
        'usuarios.CustomUser',
        through='cliente_usuario.Usuario_Cliente',
        related_name='clientes',
        help_text="Usuarios asociados al cliente mediante tabla intermedia"
    )

    def __str__(self):
        """Representación legible del objeto"""
        return self.nombre
