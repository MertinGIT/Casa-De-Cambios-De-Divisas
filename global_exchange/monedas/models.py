from django.db import models


class Moneda(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    abreviacion = models.CharField(max_length=10, unique=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre}"
