from django.db import models
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio

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

    # 💰 ganancia de la casa por esta transacción
    ganancia = models.DecimalField(max_digits=23, decimal_places=8, default=0)
    
    def _str_(self):
        return f"Transacción {self.id} - {self.tipo.upper()} {self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"