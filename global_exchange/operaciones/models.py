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


class TransaccionQuerySet(models.QuerySet):
    """QuerySet con helpers de filtrado temporal."""

    def recientes(self, limite=5, usuario=None):
        """
        Devuelve las últimas 'limite' transacciones.
        Si se pasa usuario, se filtra por ese usuario.
        """
        qs = self.order_by('-fecha')
        if usuario is not None:
            qs = qs.filter(usuario=usuario)
        return qs[:limite]


class TransaccionManager(models.Manager):
    """Manager que expone atajos basados en TransaccionQuerySet."""

    def get_queryset(self):
        return TransaccionQuerySet(self.model, using=self._db)

    def recientes(self, limite=5, usuario=None):
        """
        Delegación a QuerySet.recientes para mantener API uniforme.
        """
        return self.get_queryset().recientes(limite=limite, usuario=usuario)


class Transaccion(models.Model):
    """
    Representa una operación de cambio:
      - compra: el sistema compra moneda extranjera (usuario entrega extranjera, recibe PYG)
      - venta: el sistema vende moneda extranjera (usuario entrega PYG, recibe extranjera)
    Trazabilidad:
      - tasa_usada guarda la tasa puntual aplicada.
      - tasa_ref enlaza al registro de la tabla de cotizaciones vigente en ese momento.
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

    objects = TransaccionManager()

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