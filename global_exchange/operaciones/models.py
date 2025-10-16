"""
Modelo de operaciones (Transaccion):
- QuerySet y Manager personalizados para obtener rápidamente las últimas transacciones.
- Método de clase Transaccion.ultimas para consumo directo en vistas.
Estructura:
  TransaccionQuerySet.recientes(limite, usuario)
  TransaccionManager.recientes(...)
  Transaccion.ultimas(...)
Campos clave:
  tipo: 'compra' (cliente trae moneda extranjera y recibe PYG) / 'venta' (cliente entrega PYG y recibe extranjera)
  estado: flujo de vida de la operación (pendiente, confirmada, cancelada_*).
  tasa_usada: tasa congelada al iniciar (permite auditing).
  tasa_ref: FK a la tabla de cotizaciones para trazabilidad.
"""

from django.db import models
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from clientes.models import Cliente
from metodos_pagos.models import MetodoPago
from django.conf import settings
from django.utils import timezone

class TransaccionQuerySet(models.QuerySet):
    """
    Conjunto de consultas personalizadas para el modelo Transaccion.

    Métodos
    -------
    recientes(limite=5, usuario=None)
        Devuelve las transacciones más recientes, opcionalmente filtradas por usuario.
    """
    def recientes(self, limite=5, usuario=None):
        """
        Obtiene las transacciones más recientes.

        Parameters
        ----------
        limite : int, opcional
            Número máximo de transacciones a devolver (por defecto 5).
        usuario : User, opcional
            Usuario para filtrar las transacciones. Si no se especifica,
            devuelve las transacciones de todos los usuarios.

        Returns
        -------
        QuerySet
            Conjunto de transacciones ordenadas por fecha descendente.
        """
        qs = self.order_by('-fecha')
        if usuario is not None:
            qs = qs.filter(usuario=usuario)
        return qs[:limite]


class TransaccionManager(models.Manager):
    """
    Administrador personalizado para el modelo Transaccion.

    Sobrescribe el queryset por defecto para utilizar TransaccionQuerySet
    y expone métodos de consulta especializados.
    """

    def get_queryset(self):
        return TransaccionQuerySet(self.model, using=self._db)

    def recientes(self, limite=5, usuario=None):
        """
        Delegación a QuerySet.recientes para mantener API uniforme.
        """
        return self.get_queryset().recientes(limite=limite, usuario=usuario)


class Transaccion(models.Model):
    """
    Representa una operación de cambio de moneda realizada por un usuario.

    Este modelo guarda la información de cada transacción, incluyendo
    el usuario que la realiza, las monedas origen y destino, la tasa usada,
    el monto y el estado actual de la operación.

    Atributos:
        usuario (CustomUser): Usuario que realiza la transacción. Puede ser None.
        id (int): Identificador único de la transacción.
        fecha (datetime): Fecha y hora en que se creó la transacción.
        monto (Decimal): Cantidad de dinero involucrada en la transacción.
        tipo (str): Tipo de operación: "compra" o "venta".
        estado (str): Estado actual de la transacción. Valores posibles:
            - "pendiente"
            - "confirmada"
            - "cancelada_cotizacion"
            - "cancelada_usuario"
        moneda_origen (Moneda): Moneda desde la cual se hace la conversión.
        moneda_destino (Moneda): Moneda a la cual se convierte el monto.
        tasa_usada (Decimal): Tasa de cambio congelada al iniciar la operación.
        tasa_ref (TasaDeCambio): Referencia a la tasa vigente utilizada.
    """

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("cancelada_cotizacion", "Cancelada por cambio de cotización"),
        ("cancelada_usuario", "Cancelada por decisión del usuario"),
    ]

    TIPOS = [
        ("compra", "Compra"),
        ("venta", "Venta"),
        ('cambio', 'Cambio'),
    ]

    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="transacciones",
        null=True,
        blank=True,
        help_text="Usuario que originó la transacción (nullable para registros migrados)."
    )

    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de creación (auto)."
    )
    monto = models.DecimalField(
        max_digits=23,
        decimal_places=8,
        help_text="Monto base de la operación (interpretable según tipo)."
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPOS,
        help_text="Compra o venta."
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default="pendiente",
        help_text="Estado del ciclo de vida."
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,  # evita que se elimine un método usado en transacciones
        related_name="transacciones",
        help_text="Método de pago utilizado en la transacción (ej: efectivo, transferencia)."
    )
    ganancia = models.DecimalField(
        max_digits=23,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Ganancia obtenida por la casa de cambio en esta transacción."
    )


    moneda_origen = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name="transacciones_origen",
        help_text="Moneda que el usuario entrega."
    )
    moneda_destino = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name="transacciones_destino",
        help_text="Moneda que el usuario recibe."
    )

    tasa_usada = models.DecimalField(
        max_digits=23,
        decimal_places=8,
        help_text="Tasa concreta aplicada (con margen/comisión)."
    )
    tasa_ref = models.ForeignKey(
        TasaDeCambio,
        on_delete=models.PROTECT,
        help_text="Referencia a la cotización base vigente al iniciar."
    )

    cliente = models.ForeignKey(   # 👈 nuevo campo
        Cliente,
        on_delete=models.CASCADE,
        related_name="transacciones",
        help_text="Cliente al que pertenece esta transacción."
    )
    
    # Nuevos campos para auditoría
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    procesado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_procesadas'
    )

    
    def __str__(self):
        """
        Devuelve una representación legible de la transacción.

        :return: String con la información de la transacción.
        :rtype: str
        :example: "Transacción 1 - COMPRA 1000 Dólar -> Guaraní [pendiente]"
        """
        return f"Transacción {self.id} - {self.tipo.upper()} {self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"


    objects = TransaccionManager()
    def puede_procesarse(self):
        """Verifica si la transacción puede ser procesada"""
        return self.estado.lower() == 'pendiente' and self.metodo_pago.nombre.lower()  == 'efectivo'
    
    def procesar(self, usuario):
        """Marca la transacción como confirmada"""
        if not self.puede_procesarse():
            raise ValueError("La transacción no puede ser procesada")
        
        self.estado = 'confirmada'
        self.fecha_procesado = timezone.now()
        self.procesado_por = usuario
        self.save()
    
    def cancelar(self, usuario):
        """Cancela la transacción"""
        if self.estado == 'confirmada':
            raise ValueError("No se puede cancelar una transacción confirmada")
        
        self.estado = 'cancelada'
        self.fecha_procesado = timezone.now()
        self.procesado_por = usuario
        self.save()


    class Meta:
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["-fecha"]),
            models.Index(fields=["estado"]),
        ]
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"

    @classmethod
    def ultimas(cls, limite=5, usuario=None):
        """
        Shortcut público: retorna últimas 'limite' transacciones.
        Opcionalmente filtradas por usuario.
        """
        return cls.objects.recientes(limite=limite, usuario=usuario)

    def __str__(self):
        return (
            f"Transacción {self.id} - {self.tipo.upper()} "
            f"{self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"
        )