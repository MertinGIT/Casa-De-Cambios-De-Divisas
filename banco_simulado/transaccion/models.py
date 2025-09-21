from django.db import models

class Cliente(models.Model):
    email = models.EmailField(unique=True)   # ahora el identificador es el email
    saldo = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.email} - Saldo: {self.saldo}"


class Transaccion(models.Model):
    email = models.EmailField()  # referencia al cliente por correo
    monto = models.FloatField()
    moneda = models.CharField(max_length=10)  # PYG, USD, EUR
    tipo = models.CharField(max_length=10)   # debito / credito
    estado = models.CharField(max_length=20, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=20, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
