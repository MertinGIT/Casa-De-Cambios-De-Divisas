from django.db import models
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio

class TransaccionQuerySet(models.QuerySet):
    def recientes(self, limite=5, usuario=None):
        qs = self.order_by('-fecha')
        if usuario is not None:
            qs = qs.filter(usuario=usuario)
        return qs[:limite]

class TransaccionManager(models.Manager):
    def get_queryset(self):
        return TransaccionQuerySet(self.model, using=self._db)
    def recientes(self, limite=5, usuario=None):
        return self.get_queryset().recientes(limite=limite, usuario=usuario)

class Transaccion(models.Model):
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

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transacciones", null=True, blank=True)
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)  # fecha de creación
    monto = models.DecimalField(max_digits=23, decimal_places=8)

    tipo = models.CharField(max_length=10, choices=TIPOS)  # compra o venta
    estado = models.CharField(max_length=30, choices=ESTADOS, default="pendiente")

    # 🔑 info extra para control de cotización
    moneda_origen = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="transacciones_origen")
    moneda_destino = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="transacciones_destino")
    
    tasa_usada = models.DecimalField(max_digits=23, decimal_places=8)  # tasa congelada al iniciar la operación
    tasa_ref = models.ForeignKey(TasaDeCambio, on_delete=models.PROTECT)  # referencia a la tasa vigente

    objects = TransaccionManager()

    class Meta:
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["-fecha"]),
            models.Index(fields=["estado"]),
        ]

    @classmethod
    def ultimas(cls, limite=5, usuario=None):
        return cls.objects.recientes(limite=limite, usuario=usuario)

    def __str__(self):
        return f"Transacción {self.id} - {self.tipo.upper()} {self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"
